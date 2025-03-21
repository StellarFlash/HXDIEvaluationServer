sequenceDiagram
    participant Client as 客户端
    participant API as FastAPI应用
    participant Router as 路由模块
    participant Manager as Manager类
    participant DB as 数据库

    Client->>API: HTTP请求
    API->>Router: 路由匹配
    Router->>Manager: 调用方法
    Manager->>DB: 数据库操作
    DB-->>Manager: 返回数据
    Manager-->>Router: 返回结果
    Router-->>API: 返回响应
    API-->>Client: HTTP响应
