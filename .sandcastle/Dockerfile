FROM node:20-bookworm

# Toolchain for the bomber-memorial-site build + ralph tasks:
#  - python3 + pip: prebuild chain (section-relevancy-scorer.py etc.)
#  - imagemagick + webp + pngquant + jpegoptim: image-compression tasks (#145)
#  - git/curl/jq: sandcastle Forgejo plumbing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    imagemagick \
    webp \
    pngquant \
    jpegoptim \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code

RUN userdel -r node \
  && groupadd --gid 1000 agent \
  && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash agent \
  && git config --system safe.directory '*' \
  && mkdir -p /home/agent/workspace \
  && chown -R 1000:1000 /home/agent

USER agent
WORKDIR /home/agent/workspace
CMD ["sleep", "infinity"]
