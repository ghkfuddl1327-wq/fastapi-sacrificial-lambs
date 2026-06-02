# fastapi-scan-targets

학습용 FastAPI 샘플 2개. 모두 인메모리 `dict` 저장소 + 시드 데이터로 동작하며,
외부 DB 없이 바로 실행할 수 있습니다.

## 구조

```
fastapi-scan-targets/
├── app_a_todo/
│   └── main.py        # Todo/메모 API (중첩 JSON, 9 ops)
├── app_b_commerce/
│   └── main.py        # 커머스 API (복잡 경로 + 다수 쿼리, 9 ops)
├── requirements.txt
└── README.md
```

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
# app_a (Todo/메모) → http://127.0.0.1:8001
uvicorn main:app --app-dir app_a_todo --port 8001 --reload

# app_b (커머스) → http://127.0.0.1:8002
uvicorn main:app --app-dir app_b_commerce --port 8002 --reload
```

- Swagger UI: http://127.0.0.1:8001/docs , http://127.0.0.1:8002/docs
- OpenAPI 스펙: http://127.0.0.1:8001/openapi.json , http://127.0.0.1:8002/openapi.json

## app_a_todo — Todo/메모 API (중첩 JSON)

중첩 구조(`owner`, `tags[]`, `subtasks[]`, `metadata{}`)를 포함한 9개 오퍼레이션.

| Method | Path                          | 설명 |
| ------ | ----------------------------- | ---- |
| GET    | `/health`                     | 헬스체크 + 개수 |
| GET    | `/todos`                      | 목록 (status / owner_id / limit 필터) |
| POST   | `/todos`                      | 생성 |
| GET    | `/todos/{todo_id}`            | 단건 조회 |
| PUT    | `/todos/{todo_id}`            | 전체 수정 |
| PATCH  | `/todos/{todo_id}/status`     | 상태만 변경 |
| DELETE | `/todos/{todo_id}`            | 삭제 |
| GET    | `/todos/{todo_id}/subtasks`   | 서브태스크 목록 |
| POST   | `/todos/{todo_id}/subtasks`   | 서브태스크 추가 |

## app_b_commerce — 커머스 API (복잡 경로 + 다수 쿼리)

다중 쿼리 파라미터, 다단계 경로, 버전 세그먼트(`/items/{id}/v1/status`)를 포함한 9개 오퍼레이션.

| Method | Path                                          | 설명 |
| ------ | --------------------------------------------- | ---- |
| GET    | `/health`                                     | 헬스체크 + 개수 |
| GET    | `/products`                                   | 검색/필터/정렬/페이징 (q, category_id, brand, min_price, max_price, in_stock, tag, sort_by, order, page, page_size) |
| GET    | `/products/{product_id}`                      | 단건 조회 |
| GET    | `/products/{product_id}/variants`             | 변형 목록 |
| GET    | `/products/{product_id}/variants/{variant_id}`| 변형 단건 |
| GET    | `/items/{item_id}/v1/status`                  | 재고 상태 (include_variants) |
| GET    | `/products/{product_id}/reviews`              | 리뷰 (min_rating, page, page_size) |
| GET    | `/categories/{category_id}/products`          | 카테고리별 상품 (in_stock, limit) |
| GET    | `/products/{product_id}/related`              | 연관 상품 (limit) |
