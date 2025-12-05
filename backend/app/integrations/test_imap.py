# import imaplib

# HOST = "imap.mail.ru"
# PORT = 993
# USER = "caspianhelp@mail.ru"
# PASSWORD = "kVvt6rZs2RDabURJXLba"

# imap = imaplib.IMAP4_SSL(HOST, PORT)
# try:
#     imap.login(USER, PASSWORD)
#     print("LOGIN OK")
# except imaplib.IMAP4.error as e:
#     print("LOGIN FAILED:", e)
# finally:
#     try:
#         imap.logout()
#     except Exception:
#         pass