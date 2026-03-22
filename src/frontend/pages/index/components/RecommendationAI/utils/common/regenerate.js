/** 重新生成（Regenerate）时追加在用户提问后的说明文案 */
export function regenerateSuffix(isZh) {
	return isZh
		? '\n\n（请对同一条用户问题重新生成一版回答：换角度或补充细节，避免机械重复；篇幅与展开程度应与平时完整回答相当，勿刻意缩短。）'
		: '\n\n(Regenerate a full new answer to the same user question: a different angle or more detail; do not merely repeat. Match your usual depth and length—do not intentionally shorten.)'
}
