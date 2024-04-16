from host import Host

def main():
    host = Host(verbose=True)
    while True:
        user_message = input("User: ")
        if user_message in ["exit", "quit", "bye"]:
            break
        host.chat(user_message)

if __name__ == "__main__":
    main()