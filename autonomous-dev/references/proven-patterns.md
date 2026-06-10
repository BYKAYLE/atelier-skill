# Proven Patterns — 검증된 구현 레퍼런스

> Phase 1 기획 시 기능 키워드가 매칭되면 해당 패턴의 소스를 참조하여 설계 품질을 높인다.
> 패턴은 실제 프로덕션에서 검증된 구현만 등록한다.

---

## 사용법

1. Phase 1 기획 에이전트가 기능 목록을 도출할 때 이 파일을 참조한다
2. 기능 키워드가 매칭되면 해당 패턴의 **핵심 구조**와 **소스 경로**를 기획서에 반영한다
3. Phase 2 빌더에게 소스 경로를 전달하여 구현 시 레퍼런스로 활용한다

---

## 패턴 목록

### PAT-001: 한국 결제 연동 (Toss / LemonSqueezy / Paddle)

**매칭 키워드**: 결제, 구독, payments, billing, Toss, 토스, LemonSqueezy, Paddle

**소스**: `github.com/imgompanda/FireShipZip3`

**핵심 구조**:
- `/api/webhooks/toss/` — Toss 결제 완료/실패 webhook 핸들러 (서명 검증 포함)
- `/api/webhooks/lemon/` — LemonSqueezy 구독 생성/갱신/취소 webhook
- `/api/webhooks/paddle/` — Paddle 결제 webhook
- `/api/payment/toss/confirm/` — 결제 확인 API (success/fail 리다이렉트)
- `/src/services/payment/` — 결제 로직 서비스 레이어
- `/src/lib/lemon/` — LemonSqueezy 클라이언트

**참조 포인트**:
- webhook 서명 검증 (HMAC) 필수 구현
- 결제 성공/실패/구독 갱신 각각 별도 핸들러
- 환경변수: `TOSS_SECRET_KEY`, `TOSS_CLIENT_KEY`, `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_WEBHOOK_SECRET`
- 고객 포털 (셀프 서비스 구독 관리) 패턴 포함

**기술 스택**: Next.js API Routes + TypeScript

---

### PAT-002: RAG 챗봇 (벡터 DB + 임베딩)

**매칭 키워드**: RAG, 챗봇, chatbot, 지식베이스, knowledge base, 문서 Q&A, 벡터 검색

**소스**: `github.com/imgompanda/FireShipZip3`

**핵심 구조**:
- `/api/chatbot/` — RAG 질의응답 엔드포인트
- `/api/admin/knowledge/` — 지식 베이스 CRUD
- `/api/admin/knowledge/embed/` — 문서 벡터화 (임베딩 생성)
- `/src/components/chatbot/` — 챗봇 UI 컴포넌트

**참조 포인트**:
- PostgreSQL pgvector 확장으로 벡터 저장/검색
- Google Gemini 임베딩 모델 사용 (한국어 성능 우수)
- 문서 업로드 → 청크 분할 → 임베딩 생성 → pgvector 저장 파이프라인
- 질의 시 유사도 검색 → 컨텍스트 조립 → LLM 응답 생성

**기술 스택**: Supabase (pgvector) + Vercel AI SDK + Google Gemini

**대체 가능**: Pinecone, Weaviate, Qdrant 등 전용 벡터 DB로 교체 가능

---

### PAT-003: 트랜잭셔널 이메일 (React Email)

**매칭 키워드**: 이메일, email, 알림, notification, 환영 메일, 결제 알림, transactional email

**소스**: `github.com/imgompanda/FireShipZip3`

**핵심 구조**:
- `/src/components/emails/` — React 컴포넌트 기반 이메일 템플릿
- `/src/services/email/` — 이메일 발송 서비스
- `/src/lib/resend/` — Resend API 클라이언트

**참조 포인트**:
- `@react-email/components` + `@react-email/render`로 이메일을 React 컴포넌트로 작성
- 가입 환영, 결제 성공, 결제 실패, 구독 갱신 4종 템플릿
- Resend API로 발송 (높은 전달성, 한국 IP 정상 작동)
- 환경변수: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- 도메인 검증 (DKIM, SPF) 필수

**기술 스택**: React Email + Resend

**대체 가능**: SendGrid, AWS SES, Mailgun 등으로 발송 레이어 교체 가능 (템플릿은 그대로)

---

## 패턴 추가 규칙

1. **검증 기준**: 실제 프로덕션에서 동작이 확인된 구현만 등록
2. **형식**: PAT-{번호}, 매칭 키워드, 소스, 핵심 구조, 참조 포인트, 기술 스택
3. **갱신**: 더 나은 패턴 발견 시 기존 패턴을 교체하거나 대안으로 병기
