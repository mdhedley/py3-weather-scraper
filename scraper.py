import googleapiclient.discovery
from google.cloud import storage
import base64
import urllib2
import datetime
project_id= 'providence-demo'
location= 'global'
keyring='storage'
key='mykey'
encrypted_bucket='mdh-prov-enc-bucket'
secret='dark-sky-key'
resource='projects/{}/locations/{}/keyRings/{}/cryptoKeys/{}'.format(project_id,location,keyring,key)
weather_bucket='mdh-weather-bucket'


class WeatherScraper:
    def encrypt_key(self,key):
        kms_client = googleapiclient.discovery.build('cloudkms','v1')
        crypto_keys = kms_client.projects().locations().keyRings().cryptoKeys()
        request = crypto_keys.encrypt(
            name=resource,
            body={'plaintext': base64.b64encode(key).decode('ascii')}
        )
        response = request.execute()
        ciphertext = base64.b64decode(response['ciphertext'].encode('ascii'))
        sc = storage.Client()
        bucket = sc.bucket(encrypted_bucket)
        blob = bucket.blob(secret)
        blob.upload_from_string(ciphertext)

    def decrypt_key(self):
        sc = storage.Client()
        bucket = sc.bucket(encrypted_bucket)
        blob = bucket.blob(secret)
        cipher_text = blob.download_as_string()

        kms_client = googleapiclient.discovery.build('cloudkms','v1')
        crypto_keys = kms_client.projects().locations().keyRings().cryptoKeys()
        request = crypto_keys.decrypt(
            name = resource,
            body = {
                'ciphertext': base64.b64encode(cipher_text).decode('ascii')
            }
        )
        response = request.execute()
        plaintext = base64.b64decode(response['plaintext'].encode('ascii'))
        return plaintext
    
    def storeWeather(self):
        url =  urllib2.urlopen('https://api.darksky.net/forecast/{}/33.4353,-112.3577'.format(self.decrypt_key()))
        weather = url.read()
        url.close()
        now = datetime.datetime.now()
        blob = storage.Client().bucket(weather_bucket).blob('{}/{}/{}/{}.{}.{}.{}'.format(now.year,now.month,now.day,now.hour,now.minute,now.second,now.microsecond))
        blob.upload_from_string(weather)

        






if __name__ == "__main__":
    WeatherScraper().storeWeather()