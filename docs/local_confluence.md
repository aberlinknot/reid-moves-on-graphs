# Локальная конфлюэнтность классов по модулю III при уменьшающих движениях

Пусть $\mathcal{G}$ — множество графов, а $\sim_{\mathrm{III}}$ — эквивалентность, порождённая движением $\mathrm{III}$.

Терминология см. в [notation.md](notation.md).

## 1. Уменьшающий шаг на классах

Введём отношение $\xrightarrow{\mathrm{red}}$ на классах по $\sim_{\mathrm{III}}$:

$$[G]_{\mathrm{III}} \xrightarrow{\mathrm{red}} [H]_{\mathrm{III}}$$

тогда и только тогда, когда существуют представители $G' \in [G]_{\mathrm{III}}$, $H' \in [H]_{\mathrm{III}}$ такие, что

$$G' \xrightarrow{\text{red}} H'.$$

## 2. Цепочки на классах

Обозначим через $\rightsquigarrow$ цепочки уменьшающих движений $\xrightarrow{\mathrm{red}}$ (существует путь из уменьшающих движений на классах):

$$[A]_{\mathrm{III}} \rightsquigarrow [B]_{\mathrm{III}} \quad \Longleftrightarrow \quad \exists [C_0]_{\mathrm{III}}, [C_1]_{\mathrm{III}}, \ldots, [C_n]_{\mathrm{III}} : [C_0] = [A], [C_n] = [B], [C_i] \xrightarrow{\mathrm{red}} [C_{i+1}]$$

## 3. Локальная конфлюэнтность

Отношение $\xrightarrow{\mathrm{red}}$ локально конфлюэнтно, если для любых классов $[X]_{\mathrm{III}}, [A]_{\mathrm{III}}, [B]_{\mathrm{III}}$ из

$$[X]_{\mathrm{III}} \xrightarrow{\mathrm{red}} [A]_{\mathrm{III}}, \qquad [X]_{\mathrm{III}} \xrightarrow{\mathrm{red}} [B]_{\mathrm{III}}$$

следует существование класса $[C]_{\mathrm{III}}$ такого, что

$$[A]_{\mathrm{III}} \rightsquigarrow [C]_{\mathrm{III}}, \qquad [B]_{\mathrm{III}} \rightsquigarrow [C]_{\mathrm{III}}.$$

### Замечание о корректности определения

Определение $[G]_{\mathrm{III}} \xrightarrow{\mathrm{red}} [H]_{\mathrm{III}}$ дано через существование представителей. Поэтому оно корректно как бинарное отношение на множестве классов: истинность/ложность утверждения определяется только парами классов, а не выбором конкретного представителя.

Пояснение: если $G_1 \sim_{\mathrm{III}} G_2$ и известно, что $G_1 \xrightarrow{\text{red}} H$, то для шага на классах достаточно выбрать представителем класса $[G_2]_{\mathrm{III}}$ сам граф $G_1$ (так как $G_1 \in [G_2]_{\mathrm{III}}$). Следовательно, $[G_2]_{\mathrm{III}} \xrightarrow{\mathrm{red}} [H]_{\mathrm{III}}$.

## Гипотеза

**Локальная конфлюэнтность (на факторе по $\sim_{\mathrm{III}}$).**

На множестве классов $[G]_{\mathrm{III}}$ система уменьшающих движений (удаление изолированных вершин и удаление двойников) локально конфлюэнтна.

## Следствие: Diamond Lemma (Лемма о ромбе)

**Лемма о ромбе: Локальная конфлюэнтность + Нётеровость ⇒ Конфлюэнтность.**

Если система (ортограф) с отношением $\xrightarrow{\mathrm{red}}$ локально конфлюэнтна и нётерова, то есть не имеет бесконечных цепочек (терминирует), то она конфлюэнтна. В обозначениях классов эквивалентности по $\mathrm{III}$:

для любых классов $[A]_{\mathrm{III}}, [B]_{\mathrm{III}}$ таких, что

$$[C]_{\mathrm{III}} \rightsquigarrow [A]_{\mathrm{III}} \quad \text{и} \quad [C]_{\mathrm{III}} \rightsquigarrow [B]_{\mathrm{III}}.$$

существует класс $[D]_{\mathrm{III}}$ такой, что

$$[A]_{\mathrm{III}} \rightsquigarrow [D]_{\mathrm{III}} \quad \text{и} \quad [B]_{\mathrm{III}} \rightsquigarrow [D]_{\mathrm{III}}.$$

### Приложение к нашему проекту

Если будет доказана локальная конфлюэнтность системы $\xrightarrow{\mathrm{red}}$ и терминация (нет бесконечных цепочек уменьшений), то по лемме о ромбе для каждого класса $[G]_{\mathrm{III}}$ будет существовать единственный тупиковый класс (класс по $\sim_{\mathrm{III}}$, состоящий только из тупиковых графов), в который редуцируются все графы из $[G]_{\mathrm{III}}$.

Точнее: для любого представителя $G' \in [G]_{\mathrm{III}}$ любая максимальная цепочка уменьшений

$$G' \xrightarrow{\text{red}^\sim} N$$

заканчивается в некотором тупиковом графе $N$, и все такие конечные тупиковые графы (из разных максимальных цепочек) принадлежат одному и тому же тупиковому классу $[N]_{\mathrm{III}}$ по отношению $\sim_{\mathrm{III}}$.
