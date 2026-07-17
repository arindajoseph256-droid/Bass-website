default_app_config = "$app.apps.$(echo $app | sed 's/.*/\u&/' | sed 's/_//g')Config"
