# KVNL
KVNL - Basic Serialization with Keys, Values and NewLines

The protocol described here is probably more important than the implementation itself. It is designed to be as simple as possible.

## Structure of a Message

A *line* looks like
```
key[:size]=value
```
and is terminated with a newline (i.e., `NL`, `\n`, `0x0A`), referred to as the *trailing newline*.

An *empty line* is distinct from the above definition and contains only a trailing newline.

The *key* follows the same restrictions as an identifier in C (or Python, with the addtional restriction that it can only contain ASCII characters).

The *value* is binary data. If the size is not provided, it must not include newlines, otherwise it is completely arbitrary.

The *size*, if provided, indicates the size of the value in bytes as an ASCII-encoded base-10 integer. Explicitly note the size of the value does not include the trailing newline. If the size is not provided, the value is read until the next newline, which is assumed to be the trailing newline.

A *block* is a sequence of lines terminated by an empty line.

A *message* is a sequence of blocks terminated by an empty line. Note that this means the overall structure ends with two empty lines, the first to mask the end of the last block, the second to mark the end of the message.

Higher-order constructs can be created similarly, but are not supported by the reference implementation.

## Hashing

If a key in a block is the name of a hashing algorithm (the reference implementation checks each of `hashlib.algorithms_available`, it is recommended to choose from `hashlib.algorithms_guaranteed`), then the value is treated as a hash of all preceding lines in the block, up to and including the preceding line's trailing newline. In general, this necessitates buffering data until such a line is found instead of updating the hash as data is being read, so a deserialization program could be told to anticipate the use of a particular algorithm. Lines which should not be hashed (e.g., timestamps) are included after the hash line.
