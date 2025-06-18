# AI 履歷生成器

這是一個基於 Python Flask 框架和 Gemini API 的 AI 履歷生成器。它允許使用者輸入相關資訊，然後利用 AI 自動生成履歷。

## 功能特色
*   **AI 驅動的履歷生成**：利用 Gemini API 根據使用者輸入生成專業履歷。
*   **PDF 匯出**：將生成的履歷匯出為 PDF 格式。
*   **使用者友善的介面**：提供直觀的網頁介面，方便使用者輸入和管理履歷資訊。

## 安裝與執行
1.  **安裝依賴**：
    ```bash
    pip install flask reportlab google-generativeai
    ```
2.  **設定 Gemini API 金鑰**：
    請將您的 Gemini API 金鑰設定為環境變數 `GEMINI_API_KEY`。
    *   **Windows**:
        ```bash
        set GEMINI_API_KEY=您的API金鑰
        ```
    *   **Linux/macOS**:
        ```bash
        export GEMINI_API_KEY=您的API金鑰
        ```
3.  **執行應用程式**：
    ```bash
    python resume_generator.py
    ```
    應用程式將在 `http://127.0.0.1:5000` 啟動。

## 使用方式
1.  在網頁介面中輸入您的基本設定和求職履歷設定。
2.  點擊「生成文件」按鈕，AI 將根據您的輸入生成履歷。
3.  您可以預覽生成的履歷，並選擇下載單個 PDF 或下載所有生成的 PDF。