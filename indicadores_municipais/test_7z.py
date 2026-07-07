import ftplib
import io
import py7zr
import pandas as pd
import sys

def test_7z_extract():
    print("Testing 7z extract")
    ftp = ftplib.FTP("ftp.mtps.gov.br", timeout=120)
    ftp.login()
    # Let's find a .7z file in 2024
    base_path = "/pdet/microdados/NOVO CAGED/2024/202401/"
    files = ftp.nlst(base_path)
    
    zf = [f for f in files if "CAGEDMOV" in f.upper() and f.upper().endswith(".7Z")][0]
    print(f"Downloading {zf}")
    
    buffer = io.BytesIO()
    ftp.retrbinary(f"RETR {zf}", buffer.write)
    buffer.seek(0)
    print("Downloaded, extracting...")
    
    try:
        with py7zr.SevenZipFile(buffer, mode="r") as archive:
            extracted = archive.readall()
            for name, content in extracted.items():
                print(f"Extracted {name}")
                content.seek(0)
                df = pd.read_csv(
                    content,
                    sep=";",
                    encoding="utf-8",
                    dtype=str,
                    on_bad_lines="skip",
                    nrows=5
                )
                print(df.head())
    except Exception as e:
        print(f"Error during extraction or pandas read: {e}")
        
    ftp.quit()

if __name__ == "__main__":
    test_7z_extract()
