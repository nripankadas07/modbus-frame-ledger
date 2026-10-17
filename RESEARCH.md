# Research — 17 October 2026

User: Controls engineers reviewing an offline serial capture with a device register map.

Pain: A CRC-valid byte sequence still needs explicit address context, byte order, scale and coverage evidence.

Smallest useful capability: Decode one captured Modbus RTU register response against an explicit typed CSV map.

Acceptance: Verify known CRC vectors, all byte orders, signed values, binary32 scaling, complete map coverage, CRC failure and valid exception/nonfinite/out-of-range findings.

Demand is inferred from the workflow and adjacent public evidence, not a verified request for this product. Discovery path: descriptive GitHub topics, a runnable invented example and the chronological portfolio index. No unsolicited outreach or activity manipulation.

## Current alternatives

Live GitHub repository search, sorted **Most stars**, query `modbus library` and the related broad queries recorded in [provenance](RESEARCH_PROVENANCE.json). Highest-star relevant comparable found in this inspected scope: **stephane/libmodbus**. This is not an exhaustive global ranking.

| Repository | Stars observed | Last push observed (UTC) | Archived | API license classification |
| --- | ---: | --- | --- | --- |
| [stephane/libmodbus](https://github.com/stephane/libmodbus) | 4268 | 2026-07-02T10:16:05Z | False | LGPL-2.1 |
| [pymodbus-dev/pymodbus](https://github.com/pymodbus-dev/pymodbus) | 2782 | 2026-10-16T13:01:44Z | False | NOASSERTION |
| [gavinying/modpoll](https://github.com/gavinying/modpoll) | 154 | 2026-08-19T02:49:16Z | False | MIT |

libmodbus and Pymodbus provide full client/server protocol implementations. Modpoll already supports CSV-based device configuration. The broad modbus query also returned telemetry and energy platforms; these are broader integrations, while the focused modbus library query placed libmodbus first. No capability-absence claim or device reliability comparison is made.

Use libmodbus/Pymodbus protocol code or Modpoll with appropriate device configuration.

Current README, selected source semantics and up to five issue/PR records were read. Exact observation times, source blob identities, queries and public issue URLs are in provenance. API NOASSERTION means unclassified license, not permission to copy. No third-party implementation or fixtures are bundled.

Our small Python wheel installs with one command after checkout and includes a direct example. Established alternatives have broader APIs, formats, documentation, examples and support communities. Competitor installations, time to first useful result, reliability, support response and performance were not measured. Our example only proves our documented behavior. Stars inform discovery, not quality or performance.

Portfolio distinction: No existing owned project decodes RTU response frames or typed Modbus register maps. General CSV validation and packet text tools do not provide this protocol contract.

No technical performance benchmark, speed/memory superiority or exhaustive feature-gap claim is made. Standard file formats and algorithms are not inventions of this project. Source references informed semantic review; implementation, prose and invented fixtures are original. No copied branding or sample user data is included.
