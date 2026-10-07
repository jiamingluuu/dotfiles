# DNS 与边缘服务说明

## CDN 可能在账号级停用

命令存在并不代表账号已开通 CDN。`ve cdn ListCdnDomains` 可能返回：

```text
OperationDenied.ServiceStopped: 服务处于停用状态，不支持该操作。
```

这是账号产品状态，不是参数格式错误。

## DNS、PrivateZone 与 WAF 需要真实上下文

不要用这些创建操作做通用 smoke test：

- 公网 DNS zone 需要真实域名及所有权上下文；
- PrivateZone record 需要明确绑定的 VPC；
- WAF domain 需要真实域名、后端或负载均衡上下文。
