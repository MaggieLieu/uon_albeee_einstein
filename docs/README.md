# Project Structure
There are three APIs running:
- Port 8965: Google ADK [api_server](https://google.github.io/adk-docs/runtime/api-server/)
- Port 8964: Backend API
  - Forward the init session or delete session request to the Googel ADK API.
  - Get the user prompt in text format, pass that to the Google ADK API, get the response, pass the content to Piper, and finally stream Piper's voice as a response.
  - Get the user prompt in audio format, pass that to the speech recognition library, get the transcript and pass that to the Google ADK API, get the response, pass the content to Piper, and finally stream Piper's voice as a response.
- Port 8963: Single Page WebApp API
  - HTML, CSS, JS script
 
As the webpage needs to access the user's microphone, we need that to be working on https. Therefore, we need to generate a SSL certification for LAN usage. 

Eventually, we use `nginx` to host the webpage on the Docker.
