FROM python:3.12-slim

WORKDIR /app

# The dependency is declared in requirements.txt rather than installed inline,
# and that is not cosmetic. An inline install of this package matches the
# shipped scanner rule `tool-output-instruction`, which looks for an
# imperative verb close to a word like tool / function / shell. The upload
# scan applies that rule at the `watched_file` boundary, so uploaded SOURCE is
# judged by a rule written about text coming BACK from an operation. Measured
# 2026-09-20 on the shipped notes-server: every starter was rejected on that
# one line. Keep the dependency in the file.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# A non-root uid, and 10101 rather than the application's 10001.
#
# `local_mcp_pipeline` deliberately does not force a `user:` -- these images
# are uploaded whole, and pinning a uid over one that writes outside /tmp
# crash-loops the server. So the uid has to come from this file. Measured live
# 2026-09-21, a bundled server without this line ran as uid 0 beside an
# application confined to 10001:10001.
#
# A distinct uid because this is a SIDECAR, not the app: giving it the
# application's own uid would let each read the other's files anywhere a path
# is ever shared.
# The store directory, created and handed to the runtime uid BEFORE dropping
# to it. A non-root process cannot create a directory at `/`, so without this
# the server starts, answers, and cannot write a single record.
#
# Measured live 2026-09-21 on a real install: `/data` did not exist in either
# bundled server, nothing mounted it, and `save_note` failed with
# `[Errno 13] Permission denied: '/data'`. The failure is quiet in exactly the
# wrong way -- `_read()` treats an unreadable store as an empty one, so
# `list_notes` returns `{"count": 0}` cheerfully and only the write fails. The
# starter README's "call it again and the note saves" could not have worked
# since the uid was pinned.
RUN useradd -u 10101 -M mcpsrv \
 && mkdir -p /data \
 && chown 10101:10101 /data
USER 10101:10101

CMD ["python", "server.py"]
