# Confiança e revisão humana

O limiar obrigatório é `0.90`.

```text
saída candidata → cálculo/calibração → gate
                                      ├── ≥ 0.90: entregar
                                      └── < 0.90: bloquear e revisar
```

A confiança deve ser calculada para intenção, perfil, recomendação, explicação e resposta final. O menor componente crítico pode limitar a saída final; a fórmula será definida e calibrada na Fase 4.

O caso humano deve preservar mensagem, proposta, confiança, motivos, decisão e timestamps. A correção deverá retornar ao usuário quando aplicável e alimentar QA — comportamento ausente no protótipo.

