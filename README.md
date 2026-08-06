LM TUIO is designed to deliver simple, remote management of LM Studio Server using API interfaces only. This allows for general management without the need to SSH into the server for simple operations (see downloaded model details, load/unload models, etc.).

Features:
- Connect to networked server
    - Scan subnets for API endpoints
    - Set scans/endpoints to auto-connect on start
- View list of downloaded models ready for loading
    - View details of a given model
- View actively loaded/running models on the server
- Load models
- Unload models
    - Single, multiple, or bulk unload

Known limitations:
- LM TUIO is limited in how many model parameters can be set when submitting a load request to the API. This may not provide all needed params to successfully load a given model. However, setting model default parameters within LM Studio desktop will apply these parameters when a load API call is made. So if a model needs a specific configuration that is beyond the capabilities of LM TUIO, set the configuration in the desktop application first and then continue with LM TUIO.
    - There is no native LM TUIO way to see what presets have been configured for a model on LM Studio Desktop.
