# Embedded, protocol, hardware, and wireless research

Record exact device/revision/firmware, physical setup, frequencies/channels, capture hardware/firmware, clocks, and
environment. Prefer passive capture, read-only extraction, and shielded/lab setups before any transmission or write.

## R8 - Firmware

- Hash image; identify headers, compression/encryption, partitions/filesystems, CPU/endianness, bootloader, and signatures.
- Extract recursively into derived directories while recording offsets/tools; protect against unsafe symlinks/path traversal.
- Map init/services/config/keys/update verification/web interfaces and emulate only after architecture/runtime is known.
- Validate findings on the exact build or an accurate fixture; static presence is not reachability.

## R21 - Protocol reverse

- Preserve PCAP/raw streams and endpoint roles. Identify framing, byte order, lengths, checksums, sequence/state, and errors.
- Diff controlled message pairs one variable at a time; infer fields with confidence and validate by generating/decoding samples.
- For protobuf/gRPC, recover descriptors when possible and separate transport framing from message schema.
- Deliver a field table, state machine, parser/dissector, and positive/negative fixtures.

## R28 - OT/ICS

- Document Purdue zone, process safety boundary, vendor/device/firmware, protocol, and maintenance state.
- Passive inventory first. Never send write/control/function commands without explicit lab authorization and fail-safe recovery.
- Separate protocol reachability, controller mode, authorization, process impact, and safety impact.
- Prefer offline configs/captures and vendor documentation; preserve engineering workstation artifacts read-only.

## R29 - Wi-Fi

- Record adapter/chipset/driver, band/channel, BSSID/SSID, station identities (redacted), security mode, and capture conditions.
- Passive capture and handshake/PMKID validation first; active deauth/rogue AP only in a controlled lab.
- Distinguish capture completeness, password/key recovery, association, network authorization, and downstream access.
- Keep capture hashes and exact aircrack/tshark filters; do not store real credentials in reports.

## R34 - Hardware/debug interfaces

- Photograph/map board/revision/chips/test pads; use a multimeter/logic analyzer before connecting transmit or voltage.
- Establish ground and voltage levels; identify UART/JTAG/SWD/SPI/I2C pinout and boot-state behavior.
- Read-only dump first, repeated hash for acquisition confidence, then parse firmware separately.
- Never assume voltage or drive a line from silkscreen alone; define recovery before flash/fuse writes.

## R38 - RF/SDR

- Record center frequency, sample rate, gain, antenna, clock, location/lab shielding, and raw IQ hash.
- Identify modulation/symbol timing/framing from captures; separate RF impairments from protocol semantics.
- Build offline demod/decode and validate across several captures before considering replay.
- Transmission/replay requires explicit authorization, lawful lab conditions, bounded power/frequency/time, and stop criteria.

