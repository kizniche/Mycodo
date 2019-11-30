FROM nginx:1.17.6

RUN rm /etc/nginx/nginx.conf
COPY docker/nginx/nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY docker/nginx/project.conf /etc/nginx/conf.d/

RUN mkdir -pv /var/mycodo
COPY docker/nginx/502.html /var/mycodo/
