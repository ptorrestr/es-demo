# ES demo

## Run

You need to set `max_map_count=262144`

```bash
sysctl -w vm.max_map_count=262144
```


## Q1

There are multiple alternatives to index the data in a multi-language context using ElasticSearch.

The simplest model is to build a specific index for each language (or language-country combination).
We call this approach: __multi index__.
In this scenario, the language-dependent data is analyzed using a particular strategy for the language-country combination and stored alone in a particular index.

The main benefits of this approach are the speed at query time as the index has fewer fields to examine per query.
Moreover, since there is only one index, there is no need to determine the language of the query and the solution can scale with the number of languages.

However, there are some points to consider:

- As the number of language-country combinations grows, so will the number of indices to maintain, making the addition of new languages more expensive.
- The use of storage capacity is inefficient as space can be saved if different analyzers are conducted under the same fields. This might be relevant for countries with the same language, and minor idioms between them.
- Fields whose content has mixed language are going to be replicated as many times as needed.

Another approach is to build a single index and include as many analyzers as needed for each language of interest.
In this solution (we called __multi mappings__), the fields are going to be indexed using language-aware analyzers that will consider the particularities of each language.
Then, the system will create models for each field without replicating the text.

The main gain of this approach is controlling the storage inefficiencies observed in the previous the __multi-index__ approach. Plus, it makes the support of the index simpler as there is no need to maintain several indices.

Some cons in this approach are:

- The mappings are more complex and maintaining them might get _tricky_.
- The performance of the index might get hurt, especially if the number of language-country combinations is high.

### Code for Q1

We created a simple code to index data using the __multi-index__ approach.
We assume the field `description` in our dataset is multi-language and created two fields for Spanish and Portuguese.

You can get the answer for this solution by running:

```bash
pytest tests/test_q1.py
```

## Q2

Many components play a major role when determining the relevance score between the items and the query.
Any improvement in this score will need to consider these components:

1. __The scoring (or similarity) function__: The function that determines the similarity between the query and the documents (e.g. products, shops, etc). In this regard, `BM25` is one of the most widely used heuristics and have been extensively evaluated in many use-cases. Still, there are plenty of options in the literature that can be considered for this role [1].
2. __The structure of the documents__: Historically, inverted indexes are based on flat text document retrieval. However, this can be adapted to more sophisticated scenarios where the items of interest are structured. For example, if the schema of the items is composed of three fields: _category_, _tags_, and _description_, then we can leverage the relevance of these fields using different heuristics such as weighted average, softmax, etc.
3. __Vector space and embeddings__: Typically, items are represented in the language using a _vector space_, in which each component represents a particular word or term. Since the terms of the queries are user-dependent, there are high chances new terms might appear in the query. This gap between the language of the queries and the items can be controlled using stemming (reduce a term to its root based on prefixes and suffixes) or lemmatization (similar to stemming but based on language-dependent ontologies). The same objective can be achieved by using supervised models to create word embedding models, in which the components of their vector spaces represent the semantics of the language rather than pure lexical terms.

The evaluation of the relevance score has been extensively discussed in the literature [1]. Some examples are:

- __Precision & recall @ K__: Here the retrieval process is seen as a binary classification problem, in which the system under evaluation _must determine which item is relevant at the top k positions_. The dataset consists of queries whose results have been annotated as relevant and not relevant. The problem can then be evaluated as any other classification model.
- __Mean Average Precision (mAP) @ K__: Since the user wants to have its response at the top of the result list, it is necessary to incorporate such expectation in the evaluation process. _mAP@k_ aims to resolve this by repeatedly evaluating the average precision at the top-_k_ list and then obtaining the mean among them. The average precision evaluates how well the retrieval process is obtaining relevant items at each position of the top-$k$ list. Relevant items at the top positions will have a major impact on the score than items at the end of the result list.
- __Normalized Discounted Cumulative Gain (nDCG) @ K__: Although _mAP_ considers the position of the relevant items in the result, it cannot consider the weight of relevant items, _i.e._ some items are more relevant than others. This can be solved using the well-known heuristic DCG. This evaluation compares the resulting and expected rankings and measures the divergence between them based on a logarithmic function. Since this metric measures the divergence, the relevance of the item is not limited to a binary model. Thus, we can employ graded relevance models.
- __Correlations & Kendall-$\tau$__: Since the output of the retrieval process is a ranking, we can simply measure the correlation between them and the expected ranking.

The default relevance in Lucene (and by extension ElasticSearch) is BM25. BM25 is a well-established heuristic that combines several well-known principles into a single equation: term frequency, document length and inverse document frequency [2].
Despite BM25 not being derived from any theoretical framework, it has been applied to a wide range of problems successfully.
Still, improving BM25 is possible and is largely subjected to the domain of the documents.
For example, if we consider the items to be more like _entities_ (in the sense that they are composed of fields), there are several techniques that can be used to improve the search, especially considering that entities might have relations among themselves [3].
Therefore, without any knowledge of the data and the queries, it is difficult to propose a new relevance function.

## References

- [1] Baeza-Yates, Ricardo, and Berthier Ribeiro-Neto. Modern information retrieval. Vol. 463. New York: ACM press, 1999.
- [2] Lavrenko, Victor. A generative theory of relevance. Vol. 26. Springer Science & Business Media, 2008.
- [3] Torres-Tramón, Pablo, Mohan Timilsina, and Conor Hayes. "A diffusion-based method for entity search." 2019 IEEE 13th International Conference on Semantic Computing (ICSC). IEEE, 2019.
