# pre-2.34 CSU hardening
FROM ubuntu:16.04@sha256:1f1a2d56de1d604801a9671f301190704c25d604a416f59e03c04f5c6ffee0d6
RUN apt-get update && apt-get -y install gcc