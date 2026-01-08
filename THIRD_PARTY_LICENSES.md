# Third-Party Licenses

This project uses the following third-party libraries and tools. We gratefully acknowledge the work of these projects and their contributors.

---

## LiteLLM

**License:** MIT License (non-enterprise portions)  
**Copyright:** Copyright (c) 2023 Berri AI  
**Source:** https://github.com/BerriAI/litellm

```
Portions of this software are licensed as follows:

* All content that resides under the "enterprise/" directory of this repository, 
  if that directory exists, is licensed under the license defined in "enterprise/LICENSE".
* Content outside of the above mentioned directories or restrictions above is 
  available under the MIT license as defined below.

MIT License

Copyright (c) 2023 Berri AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Note:** This project uses only the MIT-licensed portions of LiteLLM (non-enterprise features).

---

## Model Context Protocol (MCP) SDK

**License:** MIT License  
**Copyright:** Copyright (c) 2024 Anthropic, PBC  
**Source:** https://github.com/modelcontextprotocol/python-sdk

```
MIT License

Copyright (c) 2024 Anthropic, PBC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Pydantic

**License:** MIT License  
**Copyright:** Copyright (c) 2017 to present Pydantic Services Inc. and individual contributors  
**Source:** https://github.com/pydantic/pydantic

```
MIT License

Copyright (c) 2017 to present Pydantic Services Inc. and individual contributors.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## HTTPX

**License:** BSD 3-Clause License  
**Copyright:** Copyright (c) 2019, Encode OSS Ltd.  
**Source:** https://github.com/encode/httpx

```
BSD 3-Clause License

Copyright (c) 2019, Encode OSS Ltd.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

---

## Optional Dependencies

### Firebase Admin SDK (if using cloud storage)

**License:** Apache License 2.0  
**Copyright:** Copyright 2017 Google Inc.  
**Source:** https://github.com/firebase/firebase-admin-python

The Apache License 2.0 allows use, modification, and distribution with proper attribution.
Full license text: https://www.apache.org/licenses/LICENSE-2.0

---

## Summary

| Dependency | License | Compatibility |
|------------|---------|---------------|
| LiteLLM | MIT | ✅ Compatible with MIT |
| MCP SDK | MIT | ✅ Compatible with MIT |
| Pydantic | MIT | ✅ Compatible with MIT |
| HTTPX | BSD-3-Clause | ✅ Compatible with MIT |
| Firebase Admin | Apache-2.0 | ✅ Compatible with MIT |

All dependencies are compatible with our MIT license and allow:
- Commercial use
- Modification
- Distribution
- Private use

---

## Acknowledgments

This project was built for the AI Manipulation Hackathon by The Risk Takers team.

Special thanks to:
- **Berri AI** for LiteLLM - the unified LLM gateway that powers our multi-provider support
- **Anthropic** for the Model Context Protocol (MCP) SDK and ecosystem
- **Pydantic** team for the excellent data validation library
- **Encode** for the HTTPX async HTTP client

---

*Last updated: 2026-01-08*
