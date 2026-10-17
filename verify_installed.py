import pathlib,subprocess,sys,tempfile,json,hashlib,shutil
PYTHON=pathlib.Path(sys.argv[1]).absolute()
SOURCE=pathlib.Path(__file__).absolute().parent
COMMAND=PYTHON.parent/"modbus-frame-ledger"
with tempfile.TemporaryDirectory() as td:
 work=pathlib.Path(td)
 def run(args,code=0):
  p=subprocess.run([str(COMMAND),*map(str,args)],cwd=work,text=True,capture_output=True,timeout=20)
  assert p.returncode==code,(args,p.returncode,p.stdout,p.stderr)
  if code==2:
   assert not p.stdout and p.stderr,(p.stdout,p.stderr)
   return None
  return json.loads(p.stdout)
 help_result=subprocess.run([str(COMMAND),"--help"],cwd=work,capture_output=True,text=True,timeout=10)
 assert help_result.returncode==0 and "usage:" in help_result.stdout
 installed=subprocess.run([str(PYTHON),"-I","-c","import modbus_frame_ledger,pathlib,hashlib;print(hashlib.sha256(pathlib.Path(modbus_frame_ledger.__file__).read_bytes()).hexdigest())"],cwd=work,capture_output=True,text=True,check=True).stdout.strip()
 assert installed==hashlib.sha256((SOURCE/"modbus_frame_ledger.py").read_bytes()).hexdigest()
 for p in SOURCE.glob("example.*"):shutil.copyfile(p,work/p.name)
 r=run(['example.hex','example.csv','--start','0']);assert r['complete']
 assert [v['scaled_value'] for v in r['values']]==['-10','0','12.5']
 text=(work/'example.csv').read_text();(work/'partial.csv').write_text('\n'.join(text.splitlines()[:2])+'\n')
 assert len(run(['example.hex','partial.csv','--start','0'],1)['unmapped_registers'])==3
 (work/'bad.hex').write_text('01 03 02 00 01 00 00');run(['bad.hex','example.csv','--start','0'],2)
 (work/'bad.csv').write_text(text.replace('i16,AB','i16,ABCD'));run(['example.hex','bad.csv','--start','0'],2)
 run(['example.hex','example.csv'],2)
print(json.dumps({"installed_command":"modbus-frame-ledger","outside_checkout":True,"source_identity_matched":True,"contract_checks":"passed"}))
