# 기술 스택별 코딩 표준 (v5.0)

빌더 에이전트가 코드 작성 시 참조하는 스택별 필수 규칙과 안티패턴.
이 파일은 AI 학습 데이터에만 의존하지 않고, 검증된 현재 표준을 제공하기 위해 존재한다.

---

## TypeScript / JavaScript

### 필수 규칙
- `strict: true` (tsconfig) — noImplicitAny, strictNullChecks 포함
- 타입 단언(`as`) 최소화 — 타입 가드(`is`, `in`, `instanceof`) 우선
- `unknown` 우선 (`any` 사용 금지, 불가피하면 주석으로 사유 기록)
- `enum` 대신 `const` 객체 + `as const` 사용 (tree-shaking 유리)
- 비동기: `async/await` 우선 (콜백, `.then()` 체인 지양)
- 에러: `Error` 인스턴스만 throw (문자열/객체 throw 금지)

### 안티패턴
- `// @ts-ignore` → `// @ts-expect-error`로 교체 (오류 해결 시 자동 감지)
- `Object.keys()` 반환 타입 `string[]` → 타입 좁히기 필요
- `!` (non-null assertion) 남용 → 옵셔널 체이닝 + nullish coalescing 우선

---

## React (v19+)

### 필수 규칙
- 함수 컴포넌트 + Hooks만 사용 (클래스 컴포넌트 금지)
- 서버 컴포넌트 vs 클라이언트 컴포넌트 구분 (`'use client'` 명시)
- `useEffect` 의존성 배열 정확히 기재 (eslint-plugin-react-hooks 준수)
- 폼 처리: `useActionState` (React 19) 또는 제어 컴포넌트
- 최적화: `React.memo`, `useMemo`, `useCallback`은 측정 후 적용 (premature optimization 지양)
- key: DB ID 또는 고유 식별자 사용. 배열 인덱스 금지

### 안티패턴
- `forwardRef` → React 19에서 ref를 직접 props로 전달 가능
- `useEffect`로 API 호출 → 데이터 로딩 라이브러리(TanStack Query, SWR) 또는 서버 컴포넌트 우선
- `useState` + `useEffect`로 파생 상태 관리 → `useMemo`로 계산
- `Context` 남용 (전역 상태) → 상태 관리 라이브러리(Zustand, Jotai) 고려

---

## Python (3.11+)

### 필수 규칙
- 타입 힌트 필수 (함수 시그니처, 반환 타입)
- `pathlib.Path` 사용 (`os.path` 직접 호출 지양)
- f-string 사용 (`.format()`, `%` 포맷팅 지양)
- `dataclass` 또는 `pydantic.BaseModel`로 데이터 구조 정의
- 비동기: `asyncio` + `httpx` 또는 `aiohttp` (동기 `requests`는 스크립트용)
- 예외: 구체적 예외 타입 catch (`except Exception` 최소화)

### 안티패턴
- mutable default argument (`def f(x=[])`) → `None` + 함수 내 초기화
- `import *` → 명시적 import
- bare `except:` → 최소 `except Exception:`
- `global` 키워드 → 함수 인자/반환으로 전달

---

## Rust

### 필수 규칙
- `clippy` 경고를 에러로 취급 (`#![deny(clippy::all)]`)
- `unwrap()` 프로덕션 금지 → `expect("설명")` 또는 `?` 연산자
- `unsafe` 최소화 — 사용 시 `// SAFETY:` 주석으로 불변식 문서화
- 에러 처리: `thiserror` (라이브러리) 또는 `anyhow` (애플리케이션)
- `Clone` 최소화 — 참조(`&`, `&mut`)로 해결 가능하면 참조 사용
- `String` 대신 `&str` 매개변수 (소유권 불필요 시)

### 안티패턴
- `clone()` 남발 → 소유권/차용 패턴으로 해결
- `Arc<Mutex<T>>` 남발 → 채널(`mpsc`) 또는 설계 재검토
- `Box<dyn Error>` 라이브러리에서 사용 → 구체적 에러 타입 정의

---

## Java (21+)

### 필수 규칙
- Record 사용 (불변 데이터 홀더)
- Sealed class/interface 활용 (패턴 매칭)
- `var` 지역 변수 (타입이 자명한 경우)
- Stream API 우선 (for 루프 대신, 가독성 향상 시)
- Spring Boot 3.x: `ProblemDetail` (RFC 7807) 에러 응답
- JPA: `@Transactional` 범위 최소화, N+1 쿼리 방지 (fetch join)

### 안티패턴
- `@Autowired` 필드 주입 → 생성자 주입
- raw 타입 (`List` 대신 `List<String>`)
- `throws Exception` → 구체적 예외 타입
- `System.out.println` → SLF4J Logger

---

## Swift (5.9+)

### 필수 규칙
- `async/await` 구조적 동시성 사용
- `struct` 우선 (`class`는 참조 시맨틱 필요 시에만)
- SwiftUI: `@Observable` (Observation framework, iOS 17+)
- 에러 처리: `do-catch` + 구체적 에러 타입
- 네이밍: Swift API Design Guidelines 준수 (동사형 메서드, 명사형 프로퍼티)

### 안티패턴
- Force unwrap (`!`) 프로덕션 금지 → `guard let`, `if let`, `??`
- `Any` 타입 남용 → 제네릭 또는 프로토콜
- Massive ViewController → MVVM 또는 Coordinator 패턴

---

## CSS / Tailwind

### 필수 규칙
- Tailwind 사용 시: `tailwind.config.js`에 디자인 토큰 정의, 하드코딩 값 지양
- 색상: CSS 변수 또는 Tailwind 테마 사용 (hex 직접 사용 최소화)
- 폰트 크기: `rem` 단위 (접근성)
- 레이아웃: Flexbox/Grid 우선 (float 금지)
- 반응형: mobile-first (`min-width` 미디어 쿼리)

### 안티패턴
- `!important` → 선택자 우선순위로 해결
- 매직 넘버 (`margin-top: 37px`) → 스페이싱 스케일 사용
- `position: absolute` 남용 → Flexbox/Grid로 해결 가능한지 먼저 확인

---

## 웹 데이터 수집 (Web Scraping / Crawling)

크롤링/스크래핑이 필요한 서비스(가격 비교, 데이터 수집, 모니터링, 경쟁사 분석 등)를 만들 때 적용한다.

### 권장 라이브러리: Scrapling

**왜 Scrapling인가**: 적응형 셀렉터(사이트가 변해도 요소를 자동 재탐색) + 안티봇 우회 내장 + 3단계 페처 에스컬레이션을 하나의 라이브러리로 제공한다. `pip install scrapling` 으로 설치.

### 필수 규칙

#### 3단계 페처 에스컬레이션 패턴
보호 수준이 낮은 방법부터 시도하고, 차단당하면 다음 단계로 올린다:

```python
from scrapling import Fetcher, DynamicFetcher, StealthyFetcher

# 1단계: 일반 HTTP (가장 빠르고 가벼움 — curl_cffi 기반)
page = Fetcher.get(url)

# 2단계: JS 렌더링 필요 시 → 동적 브라우저 (Playwright)
page = DynamicFetcher.fetch(url)

# 3단계: 안티봇 보호 사이트 → 스텔스 브라우저 (Patchright, 60+ 스텔스 플래그)
page = StealthyFetcher.fetch(url)
```

- 1단계(Fetcher)로 먼저 시도 → JS 필요 시 2단계(DynamicFetcher) → 차단 시 3단계(StealthyFetcher)로 전환
- 서비스 내에서 사이트별로 적절한 페처 단계를 설정으로 관리

#### 적응형 셀렉터 (사이트 리디자인 대응)
```python
# 첫 실행: 요소 구조를 저장
products = page.css('.product-card', auto_save=True)

# 사이트가 리디자인된 후: 유사도 기반으로 자동 재탐색
products = page.css('.product-card', adaptive=True, auto_save=True)
```

- 크롤링 대상 사이트의 핵심 셀렉터에는 반드시 `auto_save=True` 적용
- 주기적 크롤링 서비스에는 `adaptive=True` 필수 (사이트 변경 자동 대응)

#### 반복 요소 자동 추출 (find_similar)
```python
# 하나의 상품 카드를 찾으면 → 같은 구조의 모든 카드를 자동 발견
first_product = page.css('.product-card').first
all_products = first_product.find_similar()
```

- 상품 목록, 게시글 리스트, 검색 결과 등 반복 패턴 추출에 사용
- 셀렉터를 정확히 몰라도 하나만 찾으면 나머지를 자동 발견

#### 대규모 크롤링 안정성 (체크포인팅)
```python
from scrapling.spiders import Spider

class PriceSpider(Spider):
    concurrent_requests = 4
    download_delay = 1.0  # 예의 바른 크롤링
```

- 100+ 페이지 크롤링 시 Spider 프레임워크 사용 (체크포인팅으로 중단/재개 지원)
- `download_delay` 설정으로 대상 서버에 부하를 주지 않도록 함
- `concurrent_requests`로 동시 요청 수 제한

### 안티패턴
- `requests` + `BeautifulSoup` 조합 → 보호된 사이트에서 차단됨, 사이트 변경 시 깨짐
- 셀렉터 하드코딩만 → `adaptive=True` 없이는 사이트 변경 시 전체 크롤러 중단
- `time.sleep()`으로 차단 회피 → 근본 해결 아님, StealthyFetcher 사용
- User-Agent만 바꾸기 → TLS 핑거프린트, 브라우저 자동화 감지 등 다층 방어에 무력
- 동의 없는 과도한 크롤링 → robots.txt 준수, 적절한 delay 설정, 이용약관 확인
