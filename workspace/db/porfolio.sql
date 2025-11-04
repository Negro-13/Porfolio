CREATE DATABASE Porfolio;
USE Porfolio;

create table Users(
Email varchar(50),
Contraseña varchar(50)
);

create table Proyectos(
id int auto_increment primary key,
Titulo varchar(50),
Contenido text,
fecha varchar(50)
);
select * from Proyectos;
insert into Users (Email, contraseña) values
('max.avt8@gmail.com', 'porfolio13');
