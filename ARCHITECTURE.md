# Mondo アーキテクチャ

## 概要

Mondoは、Flaskをバックエンドにした四択クイズWebアプリケーションです。  
クイズの問題・選択肢・解説などはPythonモジュールで管理し、出題範囲や進行状況、回答結果はユーザーごとのセッションに保持します。本番環境ではセッションストアとしてRedisを使用します。

## システム構成

```mermaid
flowchart TD
    User[ユーザーのブラウザー]
    CDN[Vercel 静的配信]
    Function[Vercel Serverless Function<br/>api/index.py]
    Flask[Flask アプリケーション<br/>py/main.py]
    Templates[Jinja2 テンプレート<br/>templates/]
    Assets[CSS / JavaScript / 画像<br/>public/static/]
    Dataset[クイズデータ<br/>py/dataset.py]
    Redis[(Upstash Redis<br/>Flask-Session)]

    User -->|HTML画面・APIリクエスト| CDN
    CDN -->|動的リクエスト| Function
    Function --> Flask
    Flask --> Templates
    Flask --> Dataset
    Flask --> Redis
    User -->|CSS・JavaScript・画像| Assets
    User -->|fetch / Ajax| Function

