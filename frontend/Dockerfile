# Gunakan image Nginx yang ringan
FROM nginx:1.21-alpine

# Salin semua file statis dari root folder frontend ke direktori Nginx
COPY . /usr/share/nginx/html

# Ekspos port 80
EXPOSE 80

# Perintah default untuk menjalankan Nginx
CMD ["nginx", "-g", "daemon off;"]