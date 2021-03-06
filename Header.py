from telethon.errors.rpcerrorlist import UserNotParticipantError, UserBannedInChannelError, PhoneNumberBannedError, \
    UserDeactivatedBanError
from datetime import datetime, timezone
from telethon.sync import TelegramClient
from colorama import Fore
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest, GetParticipantRequest, \
    GetFullChannelRequest
from telethon.tl.types import UserStatusOnline, UserStatusRecently
from time import sleep
import os

# initial variables
PATH = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\4.0\\Group1.py')
scrape_link = 't.me/ShovDani'
target_link = 't.me/momon44'
start_date = datetime(2020, 10, 23, 1, 1, 1, tzinfo = timezone.utc)
end_date = datetime(2020, 11, 25, 1, 1, 1, tzinfo = timezone.utc)


class Sim:
    def __init__(self, ID, access_hash, phone, name):
        self.ID = ID
        self.access_hash = access_hash
        self.phone = phone
        self.name = name


def CreateSimList():  # opens the file and retrieve each sim as an object
    cards = []
    f = open(CARDS_PATH, 'r')
    for line in f.readlines():
        if len(line) != 1:
            sim_id, acc_hash, phone_number, sim_name = line.split(',')
            sim_name = str(sim_name).replace("\n", "")  # remove newline from names
            s = Sim(int(sim_id), acc_hash, phone_number, sim_name)
            cards.append(s)
    f.close()
    return cards

def CloseSimList(cards: list):  # writes the sim objects to the flie (minus the bans)
    file = open(PATH, 'w')
    for j in range(len(cards)):
        s = cards[j]
        if j == len(cards) - 1:
            file.write(str(s.ID) + ',' + s.access_hash + ',' + s.phone + ',' + s.name)
        else:
            file.write(str(s.ID) + ',' + s.access_hash + ',' + s.phone + ',' + s.name + '\n')
    file.close()


def NotMutual(c, user, group):
    try:
        c(GetParticipantRequest(channel = group, user_id = user))
        return False
    except UserNotParticipantError:
        return True


def isFull(c, group):
    return c(GetFullChannelRequest(group)).full_chat.participants_count >= 5300


def DeleteRow(phone: str):
    lst = CreateSimList()
    for sim in lst:
        if sim.phone == phone:
            lst.remove(sim)
    CloseSimList(lst)


def ClientConnect(sim: Sim):
    client = TelegramClient(sim.phone, sim.ID, sim.access_hash)

    # connect to client
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(sim.phone)
        client.sign_in(sim.phone, input(Fore.WHITE + 'Enter the code to ' + sim.name + ': '))

    print(Fore.GREEN + "Connected Succesfully!")
    client.disconnect()
    del client


def JoinOrLeave(option: bool):
    cards = CreateSimList()
    i = 0
    print(f"Number of sim cards before: {len(cards)}")
    while i < len(cards):
        try:
            sim = cards[i]
            client = TelegramClient(sim.phone, sim.ID, sim.access_hash)
            client.connect()

            if option:
                client(JoinChannelRequest(client.get_entity(target_link)))
                print(Fore.GREEN + f"{sim.name} Has Joined!")
            else:
                client(LeaveChannelRequest(client.get_entity(target_link)))
                print(Fore.GREEN + f"{sim.name} Has Left!")
            i += 1

        except (PhoneNumberBannedError, UserBannedInChannelError, UserDeactivatedBanError) as ex:
            print(Fore.BLACK + f"SIM {sim.name} GOT {type(ex).__name__}!")
            cards.remove(sim)

        except UserNotParticipantError:
            i += 1

        finally:
            sleep(2)
            client.disconnect()
            del client

    print(f"Number of sim cards after: {len(cards)}")
    CloseSimList(cards)  # clean the bans and close the file


def Init():
    print("Getting sim card list.. ")
    sim_cards = CreateSimList()

    main_phone = sim_cards[0]
    print(f"Connecting to main phone: {main_phone.name}")
    first_client = TelegramClient(main_phone.phone, main_phone.ID, main_phone.access_hash)
    first_client.connect()

    print("Getting group entities..")
    scrape_group = first_client.get_entity(scrape_link)
    first_client(JoinChannelRequest(scrape_group))
    target_group_entity = first_client.get_entity(target_link)
    target_id = target_group_entity.id

    print("Scraping group lists..")
    scrape_participants = first_client.get_participants(scrape_group, aggressive = True)
    target_participants = first_client.get_participants(target_group_entity, aggressive = True)

    filtered_participants = []
    final_participants = []

    print("Filtering From Groups..")
    for user in scrape_participants:
        if user.username is not None and not user.bot:  # if has a username and not a bot
            if not user.deleted:  # if it isn't a deleted account
                if hasattr(user.status, 'was_online') and start_date < user.status.was_online < end_date:
                    filtered_participants.append(user)
                elif type(user.status) == UserStatusOnline or type(user.status) == UserStatusRecently:
                    filtered_participants.append(user)

    for user1 in filtered_participants:
        flag = True
        for user2 in target_participants:
            if user1.id == user2.id:
                flag = False
        if flag:
            final_participants.append(user1)

    first_client.disconnect()
    del first_client

    return sim_cards, final_participants, target_id
