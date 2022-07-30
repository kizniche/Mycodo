FROM nginx:1.17.6

RUN rm /etc/nginx/nginx.conf
COPY nginx/nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/project.conf /etc/nginx/conf.d/

RUN mkdir -pv /var/mycodo
COPY nginx/502.html /var/mycodo/
