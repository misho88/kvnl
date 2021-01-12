# KVNL
KVNL - Basic Serialization with Keys, Values and NewLines

The protocol described here is probably more important than the implementation itself, which is designed to be fairly simple while handling non-blocking I/O reasonably well.

## Structure of a Message

A *line* looks like
```
key[:size]=value
```
and is terminated with a newline (i.e., `NL`, `\n`, `0x0A`), referred to as the *trailing newline*. The `[]` refer to an optional portion of text.

An *empty line* is distinct from the above definition and contains only a trailing newline.

The *key* follows mostly the same restrictions as an identifier in C (or Python, with the additional restriction that it can only contain ASCII characters). Dots `.` are also allowed, but all text adjacent to a dot must be an identifier (i.e., `.name` and `name.` are not allowed).

The *value* is binary data. If the size is not provided, it must not include newlines. Otherwise, it is completely arbitrary. Note that there must be a trailing newline whether or not the size is provided.

The *size*, if provided, indicates the size of the value in bytes as an ASCII-encoded base-10 nonnegative integer. Explicitly note the size of the value does not include the trailing newline. If the size is not provided, the value is read until the next newline, which is assumed to be the trailing newline.

A *block* is a sequence of lines terminated by an empty line.

A *message* is a sequence of blocks terminated by an empty line. Note that this means the overall structure ends with two empty lines, the first to mask the end of the last block, the second to mark the end of the message.

Higher-order constructs can be created similarly. That is, a sequence of messages would end with three empty lines.

## Hashing

If a key in a block is the name of a hashing algorithm (the reference implementation checks each of `hashlib.algorithms_available`; it is recommended to choose from `hashlib.algorithms_guaranteed`), then the value is treated as a hash of all preceding lines in the block, up to and including the preceding line's trailing newline. In general, this necessitates buffering data until such a line is found instead of updating the hash as data is being read, so a deserialization program could be told to anticipate the use of a particular algorithm. Since the hash only includes whatever precedes it, lines which should not be hashed (e.g., timestamps) can be included after the hash line.

## Examples

Basic loading and dumping:
```
>>> from kvnl import dumps_block, loads_block, new_hash
>>> print(*loads_block(b'key=value\nkey.subkey=other value\n\n'), sep='\n')
('key', b'value')
('key.subkey', b'other value')
>>> dumps_block(loads_block(b'key=value\nkey.subkey=other value\n\n'))
b'key=value\nkey.subkey=other value\n\n'
```

Sized values:
```
>>> dumps_block(dict(a=b'has \n in it').items())
b'a:11=has \n in it\n\n'
```

Hashing:
```
>>> dumps_block(dict(a=b'has \n in it').items(), hash=new_hash('md5'))
b'a:11=has \n in it\nmd5=81155cefd40e370899ea959363968df4\n\n'
>>> dumps_block(dict(a=b'b').items(), hash=new_hash('md5'), unhashed_lines=dict(x=b'y').items())
b'a=b\nmd5=6aea67367311873a8a1383e4373a0e3c\nx=y\n\n'
```

## Miscellaneous Notes

Headers can be implemented as a line of the sort `header=<improbable byte sequence>`. This can be useful for separating blocks in a live stream.

Hierarchical constructs are not supported, although since sized values are freeform, there is no issue with a value being KVNL-encoded.

Reading until a specific character without overshooting is slow, especially in a language like Python, since the read has to happen character by character. Large values should therefore always be sized.
