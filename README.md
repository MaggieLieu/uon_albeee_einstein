# Albeee Einstein - The UoN School of Physics and Astronomy Ambassador
This is Albeee Einstein, a clone of Albert Einstein. 

Albeee is prompted to answer any questions about the University of Nottingham and the School of Physics. 

## Run Docker container
0. Install Docker
1. Clone the repo.
2. `cd deployment`
3. `docker build -t uon-albeee-einstein .`
4. Run the container:
```
docker run -d \
-p PORT_YOU_WANT:80 -p PORT_YOU_WANT_2:443 \
-e "GOOGLE_API_KEY=YOUR_SECRET_API_KEY_HERE" \
-e HOST_IP=YOUR_HOST_IP_ADDRESS \
--name uon-albeee-einstein-server \
uon-albeee-einstein
```
You can get your secret API key from [Google AI Studio](https://aistudio.google.com/app/api-keys).

5. Access the page by entering the url: https://YOUR_HOST_IP_ADDRESS:PORT_YOU_WANT_2 in any web browser. It should be accessible from all devices connected to the same LAN. 

## UI Demo
On PC, the Single Page Application (SPA) looks: 
![demo_pc](/docs/img/demo_pc.png)

On phone, the SPA looks: 
![demo_phone](/docs/img/demo_phone.png)


## Disclaimer
I do not have enough knowledge to sort all the security out. So please do not host the server as public unless you know exactly what you are doing.
