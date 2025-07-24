from boofuzz import *

def main():
    session = Session(
        target=Target(
            connection=SocketConnection("172.16.124.103", 1234, proto='tcp')  # IP de tu Raspberry
        )
    )

    s_initialize("fuzz_input")
    if s_block_start("request_block"):
        s_string("CMD", fuzzable=False)
        s_delim(" ", fuzzable=False)
        s_string("FUZZME", fuzzable=True)
        s_block_end()

    session.connect(s_get("fuzz_input"))
    session.fuzz()

if __name__ == "__main__":
    main()
