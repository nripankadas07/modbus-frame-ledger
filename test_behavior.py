import struct
import unittest
from modbus_frame_ledger import analyze,crc16,exact,parse_map
H='name,address,type,order,scale,offset\n'
M=H+'temperature,0,i16,AB,0.1,0\nstatus,1,u16,AB,1,0\npressure,2,f32,ABCD,1,0\n'
def frame(data,unit=1,function=3):
    b=bytes([unit,function,len(data)])+data
    return (b+crc16(b).to_bytes(2,'little')).hex()
F=frame(bytes.fromhex('ff9c000041480000'))

class ModbusTests(unittest.TestCase):
    def test_known_crc_vectors(self):
        self.assertEqual(crc16(b'123456789'),0x4b37);self.assertEqual(crc16(bytes.fromhex('01030000000a')).to_bytes(2,'little').hex(),'c5cd')
    def test_register_map_and_exact_scaling(self):
        r=analyze(F,M,0);self.assertTrue(r['complete']);self.assertEqual([v['scaled_value'] for v in r['values']],['-10','0','12.5'])
    def test_four_byte_orders(self):
        canonical=struct.pack('>f',12.5)
        for order in ['ABCD','BADC','CDAB','DCBA']:
            wire=bytes(canonical['ABCD'.index(c)] for c in order);r=analyze(frame(wire),H+f'p,0,f32,{order},1,0\n',0);self.assertEqual(r['values'][0]['decoded'],'12.5')
    def test_two_byte_orders(self):
        r=analyze(frame(b'\x34\x12'),H+'x,0,u16,BA,1,0\n',0);self.assertEqual(r['values'][0]['decoded'],'4660')
    def test_signed_and_unsigned_32(self):
        for typ,value in [('u32','4294967295'),('i32','-1')]:
            self.assertEqual(analyze(frame(b'\xff'*4),H+f'x,0,{typ},ABCD,1,0\n',0)['values'][0]['decoded'],value)
    def test_scaled_binary32_exact_not_display_rounding(self):
        r=analyze(frame(struct.pack('>f',.1)),H+'x,0,f32,ABCD,10,-1\n',0);self.assertEqual(r['values'][0]['scaled_value'],'0.00000001490116119384765625')
    def test_nonfinite_is_finding(self):
        for v in [float('nan'),float('inf'),-float('inf')]:
            r=analyze(frame(struct.pack('>f',v)),H+'x,0,f32,ABCD,1,0\n',0);self.assertEqual(r['values'][0]['status'],'nonfinite_binary32');self.assertFalse(r['complete'])
    def test_unmapped_words_are_visible(self):
        r=analyze(F,H+'x,0,i16,AB,1,0\n',0);self.assertFalse(r['complete']);self.assertEqual([w['address'] for w in r['unmapped_registers']],[1,2,3])
    def test_outside_mapping_not_invented(self):
        r=analyze(F,H+'x,100,u16,AB,1,0\n',0);self.assertEqual(r['values'][0]['status'],'outside_response_window');self.assertIsNone(r['values'][0]['decoded'])
    def test_crc_corruption_refused(self):
        with self.assertRaisesRegex(ValueError,'CRC'):analyze(F[:-2]+'00',M,0)
    def test_exception_validated(self):
        raw=bytes([1,0x83,2]);f=(raw+crc16(raw).to_bytes(2,'little')).hex();r=analyze(f,M,0);self.assertEqual(r['exception_code'],2);self.assertFalse(r['complete'])
    def test_explicit_unit_function_context(self):
        with self.assertRaises(ValueError):analyze(F,M,0,unit=2)
        with self.assertRaises(ValueError):analyze(F,M,0,function=4)
        self.assertTrue(analyze(frame(bytes.fromhex('ff9c000041480000'),function=4),M,0,function=4)['complete'])
    def test_bad_bytecount_shape(self):
        for b in [b'\x01\x03\x03\x00\x01\x02',b'\x01\x03\x02\x00\x01\x00']:
            f=(b+crc16(b).to_bytes(2,'little')).hex()
            with self.assertRaises(ValueError):analyze(f,M,0)
    def test_overlapping_or_duplicate_names(self):
        for rows in ['a,0,u32,ABCD,1,0\nb,1,u16,AB,1,0\n','a,0,u16,AB,1,0\na,1,u16,AB,1,0\n']:
            with self.assertRaises(ValueError):parse_map(H+rows)
    def test_bad_map_shapes_and_numbers(self):
        for m in [H,H+'a,0,u16,AB,1\n',H+'a,0,u16,AB,NaN,0\n',H+'a,0,u16,XX,1,0\n',H+'a,0,u16,AB,1,0,extra\n']:
            with self.assertRaises(ValueError):parse_map(m)
    def test_address_overflow_and_invalid_context(self):
        for start in [65535,-1,True,65536]:
            with self.assertRaises(ValueError):analyze(F,M,start)
        for unit in [0,248,True]:
            with self.assertRaises(ValueError):analyze(F,M,0,unit)
    def test_whitespace_and_sorting(self):
        a=analyze(F,M,0);b=analyze(' '.join(F[i:i+2] for i in range(0,len(F),2)),H+'pressure,2,f32,ABCD,1,0\nstatus,1,u16,AB,1,0\ntemperature,0,i16,AB,0.1,0\n',0);self.assertEqual(a,b)
    def test_hex_and_input_budgets(self):
        for f in ['',F+'zz','aa'*1000]:
            with self.assertRaises(ValueError):analyze(f,M,0)

if __name__=='__main__':unittest.main()
