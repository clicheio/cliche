server {
        listen   8080;

        location / {
                try_files $uri @cliche;
        }

        location @cliche {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/cliche-uwsgi.sock;
        }
}
