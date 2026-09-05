# هندسة تطبيقات النماذج اللغوية الكبيرة

**Program code:** SDA-AIE-213  
**English title:** Large Language Model Application Engineering

## الوصف التدريبي

يهدف هذا البرنامج التدريبي إلى تمكين المشاركين من هندسة تطبيقات متكاملة فوق واجهات النماذج اللغوية الكبيرة والنماذج مفتوحة الأوزان، حيث يصمم المشاركون معماريات التطبيقات وخطوط الأوامر والقوالب والمخرجات المهيكلة واستدعاء الوظائف ودمج الأدوات، ويبنون منصات تقييم تقيس الجودة والسلامة وترصد الانحدار باستخدام المجموعات الذهبية وتقنيات النموذج كمُحكِّم، ويحسّنون زمن الاستجابة وتكلفة الرموز عبر خيارات النماذج والتخزين المؤقت، مع المقارنة بين النماذج التجارية ومفتوحة الأوزان باستخدام أدوات مثل LangChain وpydantic وvLLM. ويُختتم البرنامج ببناء تطبيق متكامل مدعوم بالنماذج اللغوية مع تقرير تقييم، بما يرسّخ الانضباط الهندسي وراء برمجيات الذكاء الاصطناعي التوليدي الموثوقة.

## الأهداف التدريبية

1- تصميم معماريات تطبيقات مبنية على واجهات النماذج اللغوية الكبيرة والنماذج مفتوحة الأوزان.
2- تنفيذ المخرجات المهيكلة واستدعاء الوظائف (Function Calling) ودمج الأدوات.
3- تطوير خطوط أوامر (Prompt Pipelines) قوية باستخدام القوالب والحواجز الوقائية.
4- بناء منصات تقييم لقياس الجودة والسلامة ورصد الانحدار.
5- تحسين زمن الاستجابة وتكلفة الرموز عبر خيارات النماذج والتخزين المؤقت.
6- المقارنة بين النماذج التجارية والنماذج مفتوحة الأوزان لحالة استخدام معينة.
7- إنجاز مشروع تطبيق متكامل مدعوم بالنماذج اللغوية الكبيرة مع تقرير تقييم.

## المحتوى والموضوعات التدريبية

أنماط معمارية تطبيقات النماذج اللغوية الكبيرة
1- فهم أنماط المعمارية الشائعة للتطبيقات المبنية على النماذج اللغوية الكبيرة.
2- تصميم معماريات تطبيقات تلائم متطلبات حالة الاستخدام المحددة.
3- إدراك الانضباط الهندسي اللازم لجعل برمجيات الذكاء الاصطناعي التوليدي موثوقة.

التعامل مع واجهات النماذج اللغوية والنماذج مفتوحة الأوزان
1- التعامل مع واجهات النماذج اللغوية التجارية مثل OpenAI وAnthropic في كود التطبيقات.
2- تشغيل النماذج مفتوحة الأوزان باستخدام أدوات مثل vLLM.
3- المقارنة بين الخيارات التجارية ومفتوحة الأوزان وفق متطلبات حالة الاستخدام.

المخرجات المهيكلة واستدعاء الوظائف
1- تنفيذ مخرجات مهيكلة يتم التحقق منها بمخططات pydantic.
2- استخدام استدعاء الوظائف (Function Calling) لربط النماذج بالأدوات والخدمات الخارجية.
3- تصميم تدفقات دمج الأدوات بما يحافظ على سلوك تطبيق قابل للتنبؤ.

خطوط الأوامر والقوالب والحواجز الوقائية
1- تطوير خطوط أوامر بالقوالب باستخدام أطر مثل LangChain.
2- تطبيق حواجز وقائية تقيّد مخرجات النماذج ضمن صيغ آمنة ومتوقعة.
3- التحسين التكراري لتصاميم الأوامر لرفع الموثوقية عبر المدخلات المختلفة.

تقييم النماذج اللغوية: المجموعات الذهبية والنموذج كمُحكِّم والمقاييس
1- بناء منصات تقييم باستخدام المجموعات الذهبية وأدوات مثل promptfoo.
2- تطبيق تقنيات النموذج كمُحكِّم (LLM-as-Judge) والمقاييس لقياس جودة المخرجات وسلامتها.
3- رصد الانحدارات عند تغيير الأوامر أو النماذج أو الإعدادات.

استراتيجيات التكلفة وزمن الاستجابة والتخزين المؤقت
1- تحليل محركات تكلفة الرموز وزمن الاستجابة في تطبيقات النماذج اللغوية.
2- تطبيق استراتيجيات التخزين المؤقت واختيار النماذج لخفض التكلفة وزمن الاستجابة.
3- الموازنة بين الجودة والتكلفة وزمن الاستجابة في البيئات الإنتاجية.

بناء تطبيق متكامل مدعوم بالنماذج اللغوية
1- تصميم وبناء تطبيق متكامل مدعوم بالنماذج اللغوية الكبيرة.
2- دمج المخرجات المهيكلة وخطوط الأوامر والحواجز الوقائية والتقييم في نظام واحد.
3- توثيق النتائج في تقرير تقييم يثبت جودة التطبيق وسلامته.

---

## Training description

This training program enables participants to engineer complete applications on top of LLM APIs and open-weight models. Participants design application architectures, prompt pipelines, templating, structured outputs, function calling, and tool integration, build evaluation harnesses that measure quality and safety and detect regression using golden sets and LLM-as-judge techniques, and optimise latency and token cost across model and caching choices, while comparing commercial and open-weight models using tools such as LangChain, pydantic, and vLLM. The program concludes with building a complete LLM-powered application accompanied by an evaluation report, establishing the engineering discipline behind reliable generative-AI software.

## Training objectives

1- Design application architectures around LLM APIs and open-weight models.
2- Implement structured outputs, function calling, and tool integration.
3- Develop robust prompt pipelines with templating and guardrails.
4- Build evaluation harnesses to measure quality, safety, and regression.
5- Optimize latency and token cost across model and caching choices.
6- Compare commercial and open-weight models for a given use case.
7- Complete a full LLM-powered application project with an evaluation report.

## Training content and topics

LLM Application Architecture Patterns
1- Understand common architecture patterns for applications built on large language models.
2- Design application architectures that fit the requirements of a given use case.
3- Recognize the engineering discipline required to make generative-AI software reliable.

Working with LLM APIs and Open-Weight Models
1- Work with commercial LLM APIs such as OpenAI and Anthropic in application code.
2- Serve open-weight models using tools such as vLLM.
3- Compare commercial and open-weight options against use-case requirements.

Structured Outputs and Function Calling
1- Implement structured outputs validated with pydantic schemas.
2- Use function calling to connect models with external tools and services.
3- Design tool-integration flows that keep application behaviour predictable.

Prompt Pipelines, Templating, and Guardrails
1- Develop prompt pipelines with templating using frameworks such as LangChain.
2- Apply guardrails that constrain model outputs to safe, expected formats.
3- Iterate on prompt designs to improve reliability across different inputs.

LLM Evaluation: Golden Sets, LLM-as-Judge, Metrics
1- Build evaluation harnesses using golden sets and tools such as promptfoo.
2- Apply LLM-as-judge techniques and metrics to measure output quality and safety.
3- Detect regressions when prompts, models, or configurations change.

Cost, Latency, and Caching Strategies
1- Analyze the drivers of token cost and latency in LLM applications.
2- Apply caching and model-selection strategies to reduce cost and response time.
3- Balance quality, cost, and latency trade-offs in production settings.

Building a Complete LLM-Powered Application
1- Architect and build a complete application powered by large language models.
2- Integrate structured outputs, prompt pipelines, guardrails, and evaluation into one system.
3- Document the results in an evaluation report that demonstrates the application's quality and safety.