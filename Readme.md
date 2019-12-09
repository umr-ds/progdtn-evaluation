# Evaluation for CADR (Context Aware DTN Routing) 

## ARP Cache overflow problem in big simulations

When simulating a high number of nodes, it occasionally happens, that the ARP table overflows. A workaround is, to increase the threshold for the garbage collector in the kernel. Because this a kernel thing, it has to be done on the host, and not inside of the container. A more detailed writeup written here: (https://www.cyberciti.biz/faq/centos-redhat-debian-linux-neighbor-table-overflow/).

The thresholds can be set in `/etc/sysctl.conf`:

```bash
sudo -s
echo "
## works best with <= 500 client computers
# Force gc to clean-up quickly
net.ipv4.neigh.default.gc_interval = 3600
 
# Set ARP cache entry timeout
net.ipv4.neigh.default.gc_stale_time = 3600
  
# Setup DNS threshold for arp 
net.ipv4.neigh.default.gc_thresh3 = 4096
net.ipv4.neigh.default.gc_thresh2 = 2048
net.ipv4.neigh.default.gc_thresh1 = 1024" >> /etc/sysctl.conf

sysctl -p
exit

sysctl net.ipv4.neigh.default.gc_thresh1
sysctl net.ipv4.neigh.default.gc_thresh2
sysctl net.ipv4.neigh.default.gc_thresh3
```


## MACI: Headless and GUI worker

This worker is available with a gui to be used during experiment development as well as a headless version for lightweight experiment runs.

### Build images
```bash
docker build -t umrds/mmdr_core_worker -f Dockerfile .
# or
docker-compose build core
```

## Standalone Quickstart
Although this container is intended to be used with MACI, it  as a standalone container for debugging. To work with the CORE GUI, the host needs to run an X11 server.

### Setup X11 on macOS
1. Install XQuartz, e.g. `brew cask install xquartz`
2. Configure X to allow connections from network clients (XQuartz -> Settings -> Security -> Allow Network Clients)

### Setup X11 on lightdm (Ubuntu 16)
Allow connections from network clients. Add to `/etc/lightdm/lightdm.conf`:

```
[SeatDefaults]
xserver-allow-tcp=true
```

... and restart lightdm using `sudo restart lightdm`.

### Setup X11 on gdm3 (Ubuntu 18)
Allow connections from network clients. Add to `/etc/gdm3/custom.conf`:

```
[security]
DisallowTCP=false
```

### Load ebtables kernel-module
```
sudo modprobe ebtables
```

### Start GUI

Add the remote docker host to the `xhost` access control list (`xhost +<DOCKER_HOST_IP>`) OR disable the access control list (`xhost +`).

The container can be started adding your IP to the DISPLAY variable:

```
docker run --rm --privileged -v /lib/modules:/lib/modules -it --cap-add=NET_ADMIN -e DISPLAY=<IP>:0 umrds/mmdr_core_worker
# or
DISPLAY=<IP>:0 docker-compose run core
```

**Hint: Docker for Mac users can use the special hostname `docker.for.mac.localhost`.**

**Attention: Linux sometimes uses other Display numbers than 0.** Checkout your Display using `echo $DISPLAY`

