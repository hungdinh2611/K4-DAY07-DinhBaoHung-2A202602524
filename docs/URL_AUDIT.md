# Rà soát nguồn — bước thu thập dữ liệu K4-L3B

## Trạng thái hiện tại: đã hoàn thành corpus thay thế (2026-09-20)

Đã chuyển nguồn sang **Open Food Network (OFN)** theo chỉ thị tiếp tục thu thập. `data/urls.csv` hiện chứa 5 URL OFN được chọn; danh sách Shopee cũ được lưu nguyên trạng tại [shopee-urls-rejected.csv](collection-evidence/shopee-urls-rejected.csv). Phần Shopee bên dưới là lịch sử rà soát, không phải trạng thái hiện tại.

### Nguồn được sử dụng

| URL chính thức | File corpus | Audience | Phạm vi |
|---|---|---|---|
| [Buyer FAQ](https://guide.openfoodnetwork.org/shopping-with-open-food-network/frequently-asked-questions) | ofn-buyer-faq.md | buyer | Các câu hỏi đầy đủ về sửa đơn, giao/nhận, tồn kho, giỏ hàng, giới hạn mua hàng; loại 4 mục xử lý tài khoản/thanh toán ngoài phạm vi |
| [Subscription Orders](https://guide.openfoodnetwork.org/shopping-with-open-food-network/regular-automated-orders) | ofn-buyer-subscriptions.md | buyer | Đơn định kỳ, thay đổi, thời điểm thu tiền và giá |
| [Refunds and Adjusting Payments](https://guide.openfoodnetwork.org/basic-features/orders/refunds-and-adjusting-payments) | ofn-seller-refunds.md | seller | Hoàn tiền toàn bộ/một phần, điều chỉnh, ngoại lệ theo phương thức thanh toán |
| [Manage Orders](https://guide.openfoodnetwork.org/basic-features/orders/view-orders) | ofn-seller-orders.md | seller | Quyền sửa/hủy đơn và trạng thái thanh toán/vận chuyển dành cho quản lý cửa hàng |
| [Subscriptions - Creating & Managing orders](https://guide.openfoodnetwork.org/basic-features/subscriptions/subscriptions-creating-and-managing-orders) | ofn-seller-subscriptions.md | seller | Tạo, sửa, tạm dừng, xóa và xử lý đơn định kỳ |

Đã tải thêm trang Shopping and Placing an Order để đánh giá nhưng không đưa vào corpus vì nội dung thiên về hướng dẫn thao tác mua sắm; không tăng số file bằng nguồn ít sát chủ đề. Năm trang được chọn đều xuất hiện trong chỉ mục `llms.txt` của nhà xuất bản. Bản Markdown chính thức có URL thêm `.md`, được chính trang/chỉ mục hướng dẫn; URL tải và URL bài gốc đều được lưu để truy vết.

### Điều khoản và robots

- Đã đọc tuyên bố sử dụng lại tại [OFN handbook — White label users](https://ofn-user-guide.gitbook.io/ofn-handbook/white-label-users): tài nguyên tri thức được công bố theo **CC BY-SA 4.0**, cho phép dùng lại với ghi công và chia sẻ bản phái sinh theo cùng giấy phép. Không suy luận giấy phép tài liệu từ AGPL của phần mềm.
- Lưu nguyên mục cấp phép, URL, tác giả và ngày lấy tại [permission.md](collection-evidence/permission.md). Corpus ghi công Open Food Network contributors trong mỗi frontmatter; giữ CC-BY-SA-4.0 và ghi rõ các thay đổi. Phạm vi giấy phép này là nội dung OFN đã chuẩn hóa, không tự áp giấy phép cho mã nguồn khác trong repo.
- [Robots OFN](https://guide.openfoodnetwork.org/robots.txt) cho phép `/`, với `Content-Signal: ai-train=yes, search=yes, ai-input=yes`. [Bản robots đã lưu](collection-evidence/ofn-robots.txt). Robots của miền handbook chuyển hướng về miền guide, đã kiểm tra chuyển hướng này.
- Chỉ đọc tài liệu công khai; không đăng nhập, không dùng API quản trị, không tải screenshot có thể chứa dữ liệu mẫu của người dùng. Các link ảnh có token CDN không được giữ trong corpus.
- [Fetch log](collection-evidence/fetch-log.json) lưu User-Agent thông qua script, thời điểm từng request/response, URL cuối, HTTP status, content type và SHA-256. Mọi tài liệu được chọn trả HTTP 200, `text/markdown`; nghỉ tối thiểu **1,100 giây sau khi response trước kết thúc**. Không crawl toàn website.

### Làm sạch và đối chiếu

Giữ nguyên tiếng Anh, không dịch/tóm tắt văn bản nguồn. Bản Markdown chính thức không chứa menu/banner/footer giao diện; đã bỏ dòng điều hướng `llms.txt`, ảnh và wrapper GitBook, giữ caption có chữ. Các tab Cash/BACS, Stripe, PayPal được chuyển thành heading riêng để không trộn điều kiện; nội dung cảnh báo được giữ nguyên. Link tương đối được đổi thành link nguồn tuyệt đối. Các mục FAQ bị loại được ghi tên đầy đủ trong [content-audit.json](collection-evidence/content-audit.json).

Đã đọc lại năm bài và các đoạn dùng cho đáp án: giữ nguyên giới hạn buyer không thêm sản phẩm mới vào đơn, quyền seller thêm sản phẩm, hoàn Stripe 3–5 ngày làm việc, giới hạn đơn Shipped, thời điểm thu tiền khi chu kỳ đóng, điều kiện xóa/tạm dừng subscription. Các ngày 2020 trong ví dụ subscription là ngày minh họa, không phải phiên bản. Nguồn không nêu ngày hiệu lực/phiên bản bài nên dùng `not-stated`.

Lưu ý chất lượng nguồn: ví dụ thiếu hàng trong Manage Orders nêu nhu cầu 5kg và chỉ thu hoạch 2kg nhưng dùng từ “half” khi nói giảm đơn. Giữ nguyên ví dụ theo nguồn, không tự sửa số liệu; không chọn phép tính này làm gold answer. Corpus là snapshot hướng dẫn được lấy ngày 2026-09-20, không chứng nhận rằng mọi bản triển khai OFN có cùng phiên bản/tính năng.

Audience được tách bằng việc chọn các trang buyer và seller riêng của nguồn; không gán `both` cho tài liệu trả lời về quyền khác nhau. Trang Manage Orders vẫn dành cho seller: phần “A Customer’s view” giải thích cho người quản lý cách khách nhìn thấy trạng thái, không trao quyền quản trị cho buyer. Không cần chia nhỏ thêm chỉ để tăng số file.

### Kết quả CP2

- **5 file thật**, doc_id duy nhất và trùng tên file; **2 buyer, 3 seller**.
- Metadata bắt buộc đầy đủ; thêm category, language, attribution, giấy phép và phạm vi trích xuất.
- `data/ecommerce/sources.csv` và `data/urls.csv` khớp 1–1 với 5 file.
- 55.475 ký tự Markdown nội dung sau làm sạch; raw response chỉ ở thư mục tạm hệ điều hành, không trong `data/`.
- Hai mẫu `example.com` đã chuyển sang `docs/examples/ecommerce/`, không dùng làm dữ liệu thật.
- [5 query/đáp án](../report/benchmark_queries.json) có trích dẫn và heading kiểm chứng được. Q1 cần audience=buyer để tránh lấy quyền thêm sản phẩm của seller. Chưa chạy retrieval hoặc đo A/B.
- [Báo cáo nhóm mục 1](../report/REPORT_NHOM.md) đã điền inventory và schema theo corpus thật. R1/R2/R3 để **chưa chốt** theo phản hồi người dùng; R3 có yêu cầu chiến lược heading.
- [Checklist chạy thực tế](collection-evidence/cp2-check.txt): các kiểm tra dữ liệu đều OK. Không triển khai/chạy Giai đoạn 2.

### Chạy lại

Tại thư mục gốc repo, dùng Python của môi trường hiện có:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/collect_ofn.py
.venv/Scripts/python.exe -X utf8 scripts/prepare_ofn_corpus.py
.venv/Scripts/python.exe -X utf8 scripts/check_cp2.py
```

Hai lệnh đầu tải lại rồi dựng corpus từ cache tạm; lệnh thứ ba kiểm tra corpus/evidence đã lưu, không cần mạng. Khi nguồn thay đổi, phải đọc lại, cập nhật inventory và đáp án trước khi chấp nhận snapshot mới. Script crawler mẫu không được dùng cho bước này vì làm mất cấu trúc heading/tab của nguồn; collector riêng tận dụng Markdown chính thức để giữ cấu trúc.

---

## Lịch sử rà soát Shopee — trước khi đổi nguồn

Ngày kiểm tra: 2026-09-20. Trạng thái: **đã rà soát 10 URL; chưa hoàn thành crawl/CP2**.

Đã đọc yêu cầu được giao, `docs/DATA_COLLECTION.md`, `K4_VARIANT.md`, crawler mẫu, hai tài liệu khởi động và mẫu báo cáo nhóm.

## Kết quả kiểm tra URL

Cả 10 URL trong `data/urls.csv` trả về bài viết có tiêu đề và nội dung qua công cụ duyệt web tại thời điểm kiểm tra. Đây là kiểm tra nội dung trang, không phải xác nhận crawler Python tải được HTML đầy đủ. Không thay URL bằng đường dẫn suy đoán. Tiêu đề trong CSV đã được đối chiếu với bài viết; audience biểu thị phạm vi của trang trước khi tách tài liệu.

| Article ID | Kết quả đối chiếu và xử lý | Audience của trang |
|---|---|---|
| [77251](https://help.shopee.vn/portal/4/article/77251) | Chính sách trả hàng/hoàn tiền có quyền và nghĩa vụ của cả hai bên; sửa nhãn buyer. Nếu được sử dụng, cần tách phần người mua và người bán, giữ điều kiện chung liên quan. | both |
| [79182](https://help.shopee.vn/portal/4/article/79182) | Bài hướng dẫn người mua hủy đơn; cập nhật tiêu đề đúng bài. | buyer |
| [166085](https://help.shopee.vn/portal/4/article/166085) | Chính sách chung về mã ưu đãi, không chỉ hoàn mã khi trả hàng; sửa tiêu đề và doc_id thành shopee-voucher-policy. | buyer |
| [77243](https://help.shopee.vn/portal/4/article/77243) | Điều khoản dịch vụ điều chỉnh cả người mua và người bán; sửa nhãn buyer. | both |
| [77250](https://help.shopee.vn/portal/4/article/77250) | Chính sách vận chuyển Shopee; dùng tiêu đề của nguồn. | both |
| [77246](https://help.shopee.vn/portal/4/article/77246) | Quy định đăng bán sản phẩm; đúng nhóm người bán. | seller |
| [77247](https://help.shopee.vn/portal/4/article/77247) | Chính sách cấm/hạn chế sản phẩm; mục đối tượng áp dụng nêu người bán. | seller |
| [77245](https://help.shopee.vn/portal/4/article/77245) | Quy chế toàn sàn, rộng hơn giải quyết khiếu nại; sửa nhãn seller thành both và category thành platform-regulations. | both |
| [195504](https://help.shopee.vn/portal/4/article/195504) | Điều khoản và điều kiện người bán tham gia Shopee Mart; đúng đối tượng. | seller |
| [77252](https://help.shopee.vn/portal/4/article/77252) | Điều khoản sử dụng dịch vụ hiển thị dành cho người bán; sửa về tiêu đề nguồn. | seller |

`document_version: not-stated` được giữ ở danh sách ứng viên; chưa chứng nhận phiên bản của corpus. Khi thu thập nguồn hợp lệ cần rà lại toàn văn để ghi ngày hiệu lực/phiên bản nếu có, không dùng ngày crawl làm phiên bản.

## Điểm chặn về căn cứ sử dụng

Truy cập trực tiếp [robots.txt](https://help.shopee.vn/robots.txt) trả HTTP 200 và các chỉ thị:

```text
User-Agent:*
Allow: /

sitemap: https://help.shopee.vn/sitemap.xml
```

Tuy nhiên, mục quyền sử dụng trong [Điều khoản dịch vụ](https://help.shopee.vn/portal/4/article/77243) yêu cầu có sự đồng ý trước bằng văn bản của Shopee để thu thập hoặc sao chép nội dung bằng phương tiện tự động hoặc thủ công. Repo chưa có bằng chứng cho phép này. Do yêu cầu tại mục 2 của DATA_COLLECTION.md phải kiểm tra cả điều khoản và robots.txt, không coi Allow trong robots.txt là đủ căn cứ để đưa nội dung vào corpus.

Đã thay `public-source` bằng `permission-required` trong CSV để tránh thể hiện sai quyền sử dụng. Đây là trạng thái kiểm tra, không phải giấy phép. **Chưa chạy crawler với danh sách này**. Crawler mẫu không kiểm tra trường permission và vẫn có thể tải nếu được chạy; CSV hiện là danh sách ứng viên đã rà soát, chưa phải danh sách được duyệt để crawl.

Hướng xử lý tiếp theo: chọn nguồn khác đáp ứng yêu cầu của bài, hoặc cung cấp bằng chứng cho phép sử dụng Shopee trước khi thu thập. Không sao chép bài qua công cụ khác để bỏ qua hạn chế đã phát hiện.

## Kiểm tra CP2 hiện tại

| Yêu cầu | Kết quả |
|---|---|
| 5–10 tài liệu thật | CHƯA ĐẠT: chỉ có 2 file mẫu trong data/ecommerce, đều dùng example.com |
| Metadata bắt buộc | Hai mẫu có các trường nhưng không phải dữ liệu đã xác minh; không tính đạt |
| sources.csv khớp 1–1 | CHƯA ĐẠT: chưa có manifest corpus thật |
| Ít nhất 2 audience | Danh sách ứng viên có buyer/seller/both; corpus thật chưa có |
| Nguồn truy cập được và có căn cứ sử dụng | Đã đối chiếu nội dung 10 URL; căn cứ sử dụng chưa đạt |
| Làm sạch, giữ heading và kiểm tra số liệu | Chưa thực hiện do chưa có nguồn được duyệt |
| 5 query kiểm chứng được, có câu cần audience filter | Chưa thực hiện; không tạo gold answer từ dữ liệu mẫu |

Giữ nguyên hai file mẫu, không ghi đè bằng nội dung chưa đủ căn cứ sử dụng. Không tạo sources.csv giả hoặc ghi số ký tự của các trang chưa được thu thập.

## Phạm vi công việc sau khi có nguồn hợp lệ

1. Thu thập 5–10 tài liệu, giãn cách ít nhất 1 giây, kiểm tra điều khoản và robots của nguồn mới.
2. Làm sạch menu/footer/banner; giữ nguyên ngôn ngữ, heading, điều kiện, ngoại lệ, số liệu và thời hạn.
3. Tách phạm vi buyer/seller khi cần; lập frontmatter và sources.csv khớp từng file.
4. Chạy checklist CP2 và điền Data Inventory, Metadata Schema theo corpus thật.
5. Phân công R1 Data, R2 Benchmark, R3 Strategy theo thành viên thực tế; chưa tự gán tên hoặc xác nhận phân công. R3 phải có chiến lược theo heading. Không chạy Giai đoạn 2 trước chỉ thị tiếp theo.
