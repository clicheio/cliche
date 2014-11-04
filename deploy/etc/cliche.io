server {
        listen    8080;
        server_name    www.cliche.io;

        location / {
                return 301 https://cliche.io$request_uri;
        }
}

server {
        listen    8080;
        server_name    cliche.io;

        location / {
                if ($http_x_forwarded_proto = "http") {
                        rewrite  ^/(.*)$  https://cliche.io/$1 permanent;
                }
                try_files $uri @cliche;
        }

        location @cliche {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/cliche-uwsgi.sock;
        }
}
