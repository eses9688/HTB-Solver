#!/bin/bash
# ES 리포트 백업 스크립트 - 매일 자정 cron 대신 수동/스크립트 트리거로 실행
cd /var/es/reports || exit 1
tar czf /root/backups/reports-$(date +%s).tar.gz *
