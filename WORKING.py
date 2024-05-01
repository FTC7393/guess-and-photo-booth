import asyncio
from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream import ElementBase, ET
from slixmpp.stanza import Iq
import traceback

class SendImage(ClientXMPP):
    def __init__(self, jid, password, recipient, file_path):
        super().__init__(jid, password)

        self.recipient = recipient
        self.file_path = file_path

        # Register plugins
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0363')  # HTTP File Upload
        self.register_plugin('xep_0071')  # XHTML-IM

        # Event handlers
        self.add_event_handler("session_start", self.session_start)

    async def session_start(self, event):
        self.send_presence()
        await self.get_roster()

        try:
            # Upload the file
            url = await self['xep_0363'].upload_file(self.file_path, timeout=10)
            print(f"Uploaded file to {url}")

            message = self.make_message(mto=self.recipient)
            message['type'] = 'chat'
            message['body'] = url

            # Create the x element with the OOB namespace
            x_element = ET.Element('{jabber:x:oob}x')
            url_element = ET.SubElement(x_element, 'url')
            url_element.text = url

            # Append the custom element to the message
            message.append(x_element)

            print(message.__str__())
            '''
            <message to="+12345678900@cheogram.com" id="1e967beece5e4f86ba3aaeacf0b06b8b" xml:lang="en" type="chat">
                <body>
                    https://chatterboxtown.us:5443/upload/4ae2092272047f1e6d30aa6854eac6b566fcbe30/IrvJaHNhqomCjcXMnx39YYoCsZMLPPFdHfnFdvO2/wahoo4.png
                </body>
                <x xmlns="jabber:x:oob">
                    <url>
                        https://chatterboxtown.us:5443/upload/4ae2092272047f1e6d30aa6854eac6b566fcbe30/IrvJaHNhqomCjcXMnx39YYoCsZMLPPFdHfnFdvO2/wahoo4.png
                    </url>
                </x>
            </message>
            '''
            message.send()
            print("sent")
        except IqError as e:
            print(f"Could not upload file: {e.iq['error']['text']}")
        except IqTimeout:
            print("No response from server.")
        except Exception as e:
            print(f"Failed to send image: {e}")
            traceback.print_exc()
        finally:
            self.disconnect()

if __name__ == "__main__":
    xmpp = SendImage('user@example.com', 'pass', '+12345678900@cheogram.com', 'image.png')
    xmpp.connect()
    xmpp.process(forever=False)
