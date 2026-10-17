"""Decode one captured RTU register response against an explicit engineering CSV map."""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
import re
import struct
import sys
from fractions import Fraction
from pathlib import Path

TYPES={'u16':(1,'>H'),'i16':(1,'>h'),'u32':(2,'>I'),'i32':(2,'>i'),'f32':(2,'>f')}
HEADER=['name','address','type','order','scale','offset']

def crc16(data):
    crc=0xffff
    for byte in data:
        crc^=byte
        for _ in range(8):crc=(crc>>1)^0xa001 if crc&1 else crc>>1
    return crc

def decimal(value):
    if not isinstance(value,str) or not re.fullmatch(r'[+-]?[0-9]{1,10}(?:\.[0-9]{1,8})?',value):raise ValueError('plain bounded decimal scale/offset required')
    f=Fraction(value)
    if abs(f)>10**9:raise ValueError('scale/offset magnitude exceeds 1e9')
    return f

def exact(f):
    f=Fraction(f);n,d=f.numerator,f.denominator;sign='-' if n<0 else '';n=abs(n);whole,n=divmod(n,d);digits=[]
    while n:
        n*=10;digit,n=divmod(n,d);digits.append(str(digit))
        if len(digits)>256:raise ValueError('decimal output budget exceeded')
    return sign+str(whole)+('.'+''.join(digits) if digits else '')

def parse_map(text):
    if len(text.encode('utf-8'))>65536 or '\0' in text:raise ValueError('map exceeds 64 KiB or contains NUL')
    reader=csv.DictReader(io.StringIO(text,newline=''),strict=True)
    if reader.fieldnames!=HEADER:raise ValueError('map header must be '+','.join(HEADER))
    names=set();used=set();result=[]
    for row in reader:
        if None in row or any(v is None for v in row.values()) or len(result)>=125:raise ValueError('map shape or 125-row budget')
        row={k:v.strip() for k,v in row.items()};name=row['name'];typ=row['type']
        if not name.isprintable() or not 1<=len(name)<=128 or name in names:raise ValueError('unique printable map names required')
        if typ not in TYPES or not re.fullmatch(r'[0-9]{1,5}',row['address']):raise ValueError('unsupported type or address')
        address=int(row['address']);width=TYPES[typ][0]
        orders=('AB','BA') if width==1 else ('ABCD','BADC','CDAB','DCBA')
        if row['order'] not in orders or not 0<=address<=65536-width:raise ValueError('order or address span invalid')
        span=set(range(address,address+width))
        if span&used:raise ValueError('map register spans overlap; aliases unsupported')
        used|=span;names.add(name)
        result.append({'name':name,'address':address,'type':typ,'order':row['order'],'scale':decimal(row['scale']),'offset':decimal(row['offset'])})
    if not result:raise ValueError('at least one map row required')
    return sorted(result,key=lambda r:(r['address'],r['name']))

def analyze(frame_text,map_text,start,unit=1,function=3):
    if type(start) is not int or not 0<=start<=65535:raise ValueError('caller-supplied start address must be 0..65535')
    if type(unit) is not int or not 1<=unit<=247 or type(function) is not int or function not in (3,4):raise ValueError('unit 1..247 and function 3/4 required')
    if len(frame_text)>1024 or not re.fullmatch(r'[0-9a-fA-F\t\r\n ]+',frame_text):raise ValueError('bounded whitespace-separated hexadecimal response required')
    raw=bytes.fromhex(frame_text)
    if not 5<=len(raw)<=256:raise ValueError('RTU frame length invalid')
    if int.from_bytes(raw[-2:],'little')!=crc16(raw[:-2]):raise ValueError('CRC mismatch; no decoding issued')
    if raw[0]!=unit:raise ValueError('response unit does not match explicit context')
    rows=parse_map(map_text)
    context={'unit':unit,'function':function,'start_address':start,'address_origin':'zero-based address supplied by caller; response itself carries no start address','crc_verified':True}
    if raw[1]==function|0x80:
        if len(raw)!=5 or raw[2] not in (1,2,3,4,5,6,8,10,11):raise ValueError('malformed/unsupported exception response')
        return {'context':context,'exception_code':raw[2],'registers':[],'values':[],'unmapped_registers':[],'complete':False}
    if raw[1]!=function or not 2<=raw[2]<=250 or raw[2]%2 or len(raw)!=raw[2]+5:raise ValueError('function, byte count or frame shape invalid')
    words=list(struct.unpack('>'+'H'*(raw[2]//2),raw[3:-2]))
    if start+len(words)>65536:raise ValueError('response address span exceeds 65535')
    used=set();values=[]
    for row in rows:
        width,fmt=TYPES[row['type']];a=row['address'];item={k:v for k,v in row.items() if k not in ('scale','offset')}
        item.update(scale=exact(row['scale']),offset=exact(row['offset']))
        if a<start or a+width>start+len(words):item.update(status='outside_response_window',raw_bytes=None,decoded=None,scaled_value=None)
        else:
            i=a-start;wire=raw[3+2*i:3+2*(i+width)];order=row['order'];canonical=bytes(wire[order.index(c)] for c in 'ABCD'[:len(wire)])
            value=struct.unpack(fmt,canonical)[0];used.update(range(a,a+width));item['raw_bytes']=wire.hex()
            if isinstance(value,float) and not math.isfinite(value):item.update(status='nonfinite_binary32',decoded=None,scaled_value=None)
            else:
                f=Fraction(value);item.update(status='decoded',decoded=exact(f),scaled_value=exact(f*row['scale']+row['offset']))
        values.append(item)
    unmapped=[{'address':start+i,'unsigned_word':word,'hex':f'{word:04x}'} for i,word in enumerate(words) if start+i not in used]
    return {'context':context,'exception_code':None,'registers':[{'address':start+i,'unsigned_word':word} for i,word in enumerate(words)],'values':values,'unmapped_registers':unmapped,
        'complete':not unmapped and all(v['status']=='decoded' for v in values),
        'scope':'Offline captured bytes only. CRC is integrity checking, not authenticity. Register context/map/scale/order are caller assertions, not inferred device semantics. No ports, requests or control actions.'}

def bounded(path,limit):
    with Path(path).open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit:raise ValueError('input exceeds byte budget')
    return raw.decode('utf-8-sig')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('frame');p.add_argument('map');p.add_argument('--start',type=int,required=True);p.add_argument('--unit',type=int,default=1);p.add_argument('--function',type=int,choices=(3,4),default=3);a=p.parse_args()
    try:
        r=analyze(bounded(a.frame,1024),bounded(a.map,65536),a.start,a.unit,a.function);print(json.dumps(r,sort_keys=True,indent=2));return int(not r['complete'])
    except (ValueError,OSError,UnicodeError,csv.Error,struct.error,OverflowError) as e:
        print(json.dumps({'error':str(e)}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
