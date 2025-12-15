# FoodHub

FoodHub is the project based on UVLHub, developed by the EGC groups foodhub-1 and foodhub-2 collaboratively.
It's used as a repository of Food Models in .food files.

## Manual Installation

This guide details how to install and run the application locally on a Linux system (Ubuntu 22.04 LTS recommended).

### Prerequisites

- Python 3.12 or higher
- Git
- MariaDB

### Update the system

```bash
sudo apt update -y && sudo apt upgrade -y
```

### Clone the repo

```bash
git clone git@github.com:EGC-FoodHub/foodhub.git
cd foodhub
```

### Install MariaDB

Install the official package from Ubuntu repositories:

```bash
sudo apt install mariadb-server -y
```

Start the service:

```bash
sudo systemctl start mariadb
```

### Configure MariaDB

Run the security script:

```bash
sudo mysql_secure_installation
```

Recommended settings:
- Switch to unix_socket authentication [Y/n]: `y`
- Change the root password? [Y/n]: `y`
- New password: `uvlhubdb_root_password`
- Remove anonymous users? [Y/n]: `y`
- Disallow root login remotely? [Y/n]: `y`
- Remove test database and access to it? [Y/n]: `y`
- Reload privilege tables now? [Y/n]: `y`

### Configure databases and users

Log in to MariaDB:

```bash
sudo mysql -u root -p
```

Execute the following SQL commands to create the database and user:

```sql
CREATE DATABASE uvlhubdb;
CREATE DATABASE uvlhubdb_test;
CREATE USER 'uvlhubdb_user'@'localhost' IDENTIFIED BY 'uvlhubdb_password';
GRANT ALL PRIVILEGES ON uvlhubdb.* TO 'uvlhubdb_user'@'localhost';
GRANT ALL PRIVILEGES ON uvlhubdb_test.* TO 'uvlhubdb_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Configure app environment

#### Environment variables

Copy the example environment file:

```bash
cp .env.local.example .env
```

#### It's mandatory to change the default values of the keys in .env file, provided by us.

#### Ignore webhook module

If you are not using Docker or deployed environment, ignore the webhook module:

```bash
echo "webhook" > .moduleignore
```

### Install dependencies

#### Create and activate a virtual environment

```bash
sudo apt install python3.12-venv
python3.12 -m venv venv
source venv/bin/activate
```

#### Install Python dependencies

Upgrade pip and install requirements:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Install Rosemary (Editable mode)

Install the Rosemary CLI tool in editable mode:

```bash
pip install -e ./
```

Check installation:

```bash
rosemary
```

### Run app

#### Apply migrations

Create database tables:

```bash
flask db upgrade
```

#### Populate database

Seed the database with test data:

```bash
rosemary db:seed
```

#### Run development Flask server

Start the server:

```bash
flask run --host=0.0.0.0 --reload --debug
```

Access the application at [http://localhost:5000](http://localhost:5000).

## Deploy on Vagrant

#### Environment variables

Copy the example environment file:

```bash
cp .env.vagrant.example .env
```

#### It's mandatory to change the default values of the keys in .env file, provided by us.



#### Change to vagrant directory

```bash
cd vagrant
```
#### Set up virtual machine

```bash
vagrant up
```

#### Access to deployed project

Now, you can type http://localhost:5000 in your web browser to see it.

#### See virtual machine status

```bash
vagrant status
```

#### Stop virtual machine status

```bash
vagrant suspend
```


## Deploy on Docker

#### Environment variables

Copy the example environment file:

```bash
cp .env.docker.example .env
```

#### It's mandatory to change the default values of the keys in .env file, provided by us.

#### Stop MariaDB if running

For a correct operation, stop the current mariaDB service:

```bash
sudo systemctl stop mariadb
```

#### Build the container

Type this command to build the container:

```bash
docker compose -f docker/docker-compose.dev.yml up -d --build
```

If the container is already built, run:

```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

#### Access to deployed project

Now, you can type http://localhost in your web browser to see it.

#### Stop de container

Execute this to stop the running container:

```bash
docker compose -f docker/docker-compose.dev.yml down -v
```


## Deploy on Render

#### URL for app deployed on Render

Copy this url and paste it in your browser:

https://foodhub-gznv.onrender.com/

#### Also, these are the URLs of two subgroups:

foodhub-1:

https://foodhub-main-1.onrender.com

foodhub-2:

https://foodhub-pn1k.onrender.com

## Execution of tests

The commands to execute the different tests

### Unit Tests

```bash
rosemary test
```

### Unit Tests with coverage

```bash
rosemary coverage
```

### Selenium Tests

```bash
rosemary selenium
```

### Locust Tests

```bash
rosemary locust
```