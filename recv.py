import asyncio
from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

class MessageReceiver(ClientXMPP):
    def __init__(self, jid, password):
        super().__init__(jid, password)

        # Event handlers
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message_received)

    async def session_start(self, event):
        self.send_presence()
        await self.get_roster()
        print('ready')

    def message_received(self, msg):
        # Check if the message is 'chat' type
        if msg['type'] in ('chat', 'normal'):
            print("Received message:")
            print(msg.xml, msg.__str__())  # This prints the raw XML stanza of the message

if __name__ == "__main__":
    # Replace these with your JID and password
    xmpp = MessageReceiver('user@example.com', 'pass')
    xmpp.connect()
    asyncio.run(xmpp.process())
