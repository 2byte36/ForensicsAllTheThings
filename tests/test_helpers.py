"""Synthetic fixtures for repository-owned helpers; no challenge artifacts."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from email.message import EmailMessage

HELPERS = Path(__file__).resolve().parents[1] / 'scripts' / 'helpers'


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def run_helper(self, name, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(HELPERS / name), *map(str, args)],
                                cwd=self.root, text=True, capture_output=True, env=env)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def rows(self, result):
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_inventory_hashes_and_symlinks(self):
        tree = self.root / 'evidence'; tree.mkdir()
        (tree / 'one').write_bytes(b'abc')
        (tree / 'link').symlink_to(tree / 'one')
        rows = self.rows(self.run_helper('inventory.py', tree))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sha256'], hashlib.sha256(b'abc').hexdigest())
        self.run_helper('inventory.py', tree / 'missing', ok=False)

    def test_carve_exact_bounds_and_refuse_existing(self):
        src = self.put('source', bytes(range(32)))
        out = self.root / 'out'
        self.run_helper('carve.py', src, out, '--offset', '0x10', '--length', '16')
        self.assertEqual(out.read_bytes(), bytes(range(16, 32)))
        self.run_helper('carve.py', src, out, '--offset', '0', '--length', '1', ok=False)
        self.assertEqual(out.read_bytes(), bytes(range(16, 32)))
        self.run_helper('carve.py', src, self.root/'bad', '--offset','31','--length','2',ok=False)
        self.assertFalse((self.root/'bad').exists())

    def test_marker_overlap_and_chunk_boundary(self):
        boundary = 1024 * 1024
        src = self.put('source', b'x'*(boundary-2)+b'ABABA')
        out = self.run_helper('scan_bytes.py',src,'--text','ABA').stdout.splitlines()
        self.assertEqual([int(x.split()[0]) for x in out], [boundary-2,boundary])
        self.run_helper('scan_bytes.py',src,'--hex','',ok=False)
        empty=self.put('empty',b'')
        self.assertEqual(self.run_helper('scan_bytes.py',empty,'--text','A').stdout,'')

    def test_strict_decoding_and_xor(self):
        src=self.put('encoded',base64.b64encode(b'\x00CTF{}'))
        out=self.root/'decoded'
        self.run_helper('decode_bytes.py','base64',src,out)
        self.assertEqual(out.read_bytes(),b'\x00CTF{}')
        bad=self.put('bad',b'not#base64')
        self.run_helper('decode_bytes.py','base64',bad,self.root/'bad-out',ok=False)
        self.assertFalse((self.root/'bad-out').exists())
        hexfile=self.put('hex',b'43 54 46')
        self.run_helper('decode_bytes.py','hex',hexfile,self.root/'hexout')
        self.assertEqual((self.root/'hexout').read_bytes(),b'CTF')
        cipher=self.put('cipher',bytes(x^0x13 for x in b'hello'))
        self.run_helper('decode_bytes.py','xor',cipher,self.root/'plain','--key-hex','13')
        self.assertEqual((self.root/'plain').read_bytes(),b'hello')
        self.run_helper('decode_bytes.py','xor',cipher,self.root/'empty-key','--key-hex',' ',ok=False)

    def test_timestamp_epochs_and_precision(self):
        values={'unix':1700000000,'unix-ms':1700000000000,'unix-us':1700000000000000,
                'chromium':13344473600000000,'filetime':133444736000000001,'apple':721692800}
        for fmt,value in values.items():
            row=self.rows(self.run_helper('timestamps.py',fmt,value))[0]
            self.assertEqual(row['utc'],'2023-11-14T22:13:20+00:00')
            self.assertEqual(row['remaining_100ns_ticks'],int(fmt=='filetime'))
        self.run_helper('timestamps.py','filetime',10**30,ok=False)
        row=self.rows(self.run_helper('timestamps.py','unix',-1))[0]
        self.assertEqual(row['utc'],'1969-12-31T23:59:59+00:00')

    def test_zip_metadata_not_extraction(self):
        src=self.root/'test.zip'
        with zipfile.ZipFile(src,'w') as z:
            z.writestr('../outside.txt','bad path')
            z.writestr('ok.txt','hello')
        rows=self.rows(self.run_helper('zip_inventory.py',src))
        self.assertTrue(rows[0]['suspicious_path'])
        self.assertFalse(rows[1]['suspicious_path'])
        self.assertEqual(rows[1]['size'],5)
        self.assertFalse((self.root/'ok.txt').exists())
        self.run_helper('zip_inventory.py',self.put('invalid',b'bad'),ok=False)

    def test_browser_history_both_schemas(self):
        cases={
            'chromium':"CREATE TABLE urls(id,url,title); CREATE TABLE visits(url,visit_time); INSERT INTO urls VALUES(1,'https://example.org','title'); INSERT INTO visits VALUES(1,13344473600000000);",
            'firefox':"CREATE TABLE moz_places(id,url,title); CREATE TABLE moz_historyvisits(place_id,visit_date); INSERT INTO moz_places VALUES(1,'https://example.org','title'); INSERT INTO moz_historyvisits VALUES(1,1700000000000000);"}
        for name,schema in cases.items():
            path=self.root/(name+' #.db')
            conn=sqlite3.connect(path); conn.executescript(schema); conn.close()
            before=path.read_bytes()
            rows=self.rows(self.run_helper('browser_history.py',name,path))
            self.assertEqual(rows[0]['utc'],'2023-11-14 22:13:20')
            self.assertEqual(path.read_bytes(),before)
            self.run_helper('browser_history.py',name,path,'--limit','0',ok=False)
        self.run_helper('browser_history.py','firefox',self.root/'chromium #.db',ok=False)

    def test_real_sqlite_wal_and_corruption(self):
        db=self.root/'db'
        conn=sqlite3.connect(db)
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE records(value)'); conn.commit()
            conn.execute("INSERT INTO records VALUES('fixture')"); conn.commit()
            raw=Path(str(db)+'-wal').read_bytes()
            wal=self.put('copy.wal',raw)
            rows=self.rows(self.run_helper('wal_frames.py',wal))
            self.assertGreater(len(rows),1)
            self.assertTrue(any(row.get('commit_db_pages',0)>0 for row in rows))
            self.assertTrue(all(row.get('checksum_valid') for row in rows[1:]))
            bad=bytearray(raw); bad[-1]^=1
            self.run_helper('wal_frames.py',self.put('bad.wal',bad),ok=False)
            self.run_helper('wal_frames.py',self.put('truncated.wal',raw[:-1]),ok=False)
            self.run_helper('wal_frames.py',self.put('header.wal',raw[:17]),ok=False)
        finally:
            conn.close()

    def test_wal_big_endian_checksum(self):
        def check(data,a=0,b=0):
            words=struct.unpack('>'+str(len(data)//4)+'I',data)
            for i in range(0,len(words),2):
                a=(a+words[i]+b)%2**32; b=(b+words[i+1]+a)%2**32
            return a,b
        head=struct.pack('>6I',0x377f0683,3007000,512,0,123,456)
        state=check(head)
        data=b'\0'*512
        fields=struct.pack('>2I',1,1)
        frame=fields+struct.pack('>2I',123,456)+struct.pack('>2I',*check(fields+data,*state))+data
        rows=self.rows(self.run_helper('wal_frames.py',self.put('big.wal',head+struct.pack('>2I',*state)+frame)))
        self.assertEqual(rows[1]['page_number'],1)

    def test_email_generated_names_and_collision(self):
        msg=EmailMessage(); msg.set_content('hello')
        msg.add_attachment(b'fixture',maintype='application',subtype='octet-stream',filename='../../escape')
        src=self.put('mail.eml',msg.as_bytes())
        directory=self.root/'attachments'
        rows=self.rows(self.run_helper('email_extract.py',src,directory))
        self.assertEqual(rows[0]['original_name'],'../../escape')
        files=list(directory.iterdir()); self.assertEqual(len(files),1)
        self.assertEqual(files[0].read_bytes(),b'fixture')
        self.run_helper('email_extract.py',src,directory,ok=False)

    @unittest.skipUnless(importlib.util.find_spec('PIL'),'Pillow not installed')
    def test_lsb_packing_and_invalid_mode(self):
        from PIL import Image
        image=Image.new('RGB',(8,1)); image.putdata([(0,0,int(bit)) for bit in '01000001'])
        path=self.root/'image.png'; image.save(path)
        self.run_helper('lsb_extract.py',path,self.root/'bits')
        self.assertEqual((self.root/'bits').read_bytes(),b'A')
        self.run_helper('lsb_extract.py',path,self.root/'no-alpha','--channel','A',ok=False)
        Image.new('P',(8,1)).save(self.root/'palette.png')
        self.run_helper('lsb_extract.py',self.root/'palette.png',self.root/'bad-mode',ok=False)

    def test_hid_shift_caps_release_and_rollover(self):
        reports=['0000040000000000','0000040000000000','0000000000000000',
                 '0200040000000000','0000000000000000','0000390000000000',
                 '0000000000000000','0000040000000000']
        src=self.put('reports.hex',('\n'.join(reports)).encode())
        rows=self.rows(self.run_helper('hid_boot_decode.py',src))
        self.assertEqual([r['text'] for r in rows],['a','A','<CAPSLOCK>','A'])
        self.run_helper('hid_boot_decode.py',self.put('rollover',b'0000010101010101'),ok=False)
        self.run_helper('hid_boot_decode.py',self.put('short',b'0000'),ok=False)

    def test_cloud_optional_fields_and_schema(self):
        src=self.put('cloud.json',json.dumps({'Records':[{'eventName':'GetObject'},{'userIdentity':{'principalId':'example'}}]}).encode())
        rows=self.rows(self.run_helper('cloudtrail_summary.py',src))
        self.assertIsNone(rows[0]['identity'])
        self.assertEqual(rows[1]['identity'],'example')
        self.run_helper('cloudtrail_summary.py',self.put('wrong.json',b'[]'),ok=False)

    def fake_executable(self,name,exitcode):
        path=self.root/name
        path.write_text(f'#!{sys.executable}\nimport sys\nprint("fixture", *sys.argv[1:])\nsys.exit({exitcode})\n')
        path.chmod(0o755)
        return path

    def test_memory_wrapper_success_and_failure(self):
        memory=self.put('memory.raw',b'fixture')
        executable=self.fake_executable('fake-vol',0)
        self.run_helper('memory_triage.py',memory,self.root/'reports','--vol',executable)
        self.assertEqual(len(list((self.root/'reports').glob('*.txt'))),10)
        executable=self.fake_executable('bad-vol',2)
        self.run_helper('memory_triage.py',memory,self.root/'failed','--vol',executable,ok=False)

    def test_packet_wrapper_success_and_failure(self):
        capture=self.put('capture',b'fixture')
        self.fake_executable('tshark',0)
        env=dict(os.environ,PATH=str(self.root)+os.pathsep+os.environ.get('PATH',''))
        self.run_helper('pcap_summary.py',capture,self.root/'pcap','--wireless',env=env)
        self.assertTrue((self.root/'pcap/eapol.txt').exists())
        self.fake_executable('tshark',2)
        self.run_helper('pcap_summary.py',capture,self.root/'fail',env=env,ok=False)

    @unittest.skipUnless(shutil.which('tshark'),'TShark not installed')
    def test_real_tshark_empty_capture(self):
        capture=self.put('empty.pcap',struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
        self.run_helper('pcap_summary.py',capture,self.root/'real-pcap','--wireless')
        self.assertEqual((self.root/'real-pcap/dns.tsv').read_text(),'')


if __name__ == '__main__':
    unittest.main()
