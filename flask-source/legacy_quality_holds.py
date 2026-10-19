"""Exact-text holds from the 19 October 2026 review of 457 public article leads.

These 110 entries had clear subject substitutions or published generation
failures. Fingerprints keep corrected prose outside a stale review, and a
trigger-substitution hold also requires the original research query. The
legacy audit snapshots the full database record before applying any hold.
Only the startup legacy audit uses this list; new publications use the normal
subject/evidence gate. Captured leads are in the regression fixture for review.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

REVIEWED_LEGACY_HOLDS = {
    "a-significant-religious-site-in-algiers-with-layered-historical-use": {
        "lead_sha256": "3ec8e69658f8bdfcb307d55e3f962e23546c7188068b4823bfd3bc7a37e39c3c",
        "reason": "reviewed_legacy_trigger_subject_substitution: Fourteen concise facts about the letter A",
        "trigger_query": "A significant religious site in Algiers with layered historical use"
    },
    "acropolis-athens": {
        "lead_sha256": "a23a03f32233148906b47193b98ed36f2fe652f5bfd1ee028342d34c8bbaa499",
        "reason": "reviewed_legacy_evidence_failure: a factual explainer about the Acropolis cannot be produced from this evidence"
    },
    "acropolis-of-lindos": {
        "lead_sha256": "d562c2fb8d7d386b38c0527804fcb0036ddc287e376499ccec961022d9774f08",
        "reason": "reviewed_legacy_trigger_subject_substitution: The Acropolis of Athens",
        "trigger_query": "Acropolis of Lindos"
    },
    "algiers": {
        "lead_sha256": "c8dea1a334fd5c14e22fcf638251913528475ed8b3608c3c5c977e52e84726f0",
        "reason": "reviewed_legacy_wrong_subject: the provided evidence pertains to the Capital radio brand and its Scottish counterpart"
    },
    "algiers-casbah": {
        "lead_sha256": "66454a3b520c60a8b395cec944d102af11ec15ea63fcfa32b512322d22760221",
        "reason": "reviewed_legacy_evidence_failure: the sources are exclusively about a modding website"
    },
    "ammoudi-bay": {
        "lead_sha256": "59e4bb43514da813bd9e2e4b4f451960a725df500e2132eaf6fdab8dc98725da",
        "reason": "reviewed_legacy_evidence_failure: Each item states a distinct, verifiable fact about what the evidence lacks regarding this destination."
    },
    "archaeological-institute-of-america": {
        "lead_sha256": "bc6ac8dd4c75e36d8f4d855989e317c9c98684e79a600422a163614ad454758a",
        "reason": "reviewed_legacy_wrong_subject: An overview of the term ‘professional’"
    },
    "bala-hissar-kabul": {
        "lead_sha256": "0c5d5c1ec4b633be6af47941e5b3f38073a74d92a394109797b4d66dc26f6db1",
        "reason": "reviewed_legacy_evidence_failure: the items below describe what the sources lack rather than what they affirm"
    },
    "bath-city-guide": {
        "lead_sha256": "dcd4233d84259fa6e674f8bfaf366ef5d34fa0c0cff64ffece3a88dafafb35f4",
        "reason": "reviewed_legacy_evidence_failure: This guide notes that the supplied evidence does not contain any specific information about Bath."
    },
    "bath-unesco-world-heritage-site": {
        "lead_sha256": "093d945a9e9be5648af43fa9b5f4a19fa45b0233b0b2f1149dd23d914926a016",
        "reason": "reviewed_legacy_evidence_failure: do not provide specific evidence about Bath UNESCO World Heritage Site."
    },
    "battle-east-sussex": {
        "lead_sha256": "868d42265513974edc53d1b58c6e2a2268ed992280c1d9af6d5bac71684cb716",
        "reason": "reviewed_legacy_evidence_failure: none contain specific information about the town of Battle, East Sussex"
    },
    "borough-market-london": {
        "lead_sha256": "926cf84a37c0584bc7c6be53a9da987d621e532245f6e3852e92bfd29f983473",
        "reason": "reviewed_legacy_evidence_failure: Due to insufficient sourced evidence, this explainer cannot provide verified facts about Borough Market."
    },
    "british-museum": {
        "lead_sha256": "fbef663cd8b786f89205de8fafb01a9090905ac166b1f0dc14b8c8fe38d8d130",
        "reason": "reviewed_legacy_wrong_subject: the available source material concerns the abstract notion of a 'world'"
    },
    "buckingham-palace-london": {
        "lead_sha256": "60bfbd55fa97fee8cda4e702c9a663fb5b46c0233ebd0d5612de4120d472ef89",
        "reason": "reviewed_legacy_evidence_failure: fourteen distinct statements, each noting a particular aspect of Buckingham Palace that is absent from the evidence"
    },
    "butrint-albania": {
        "lead_sha256": "3dfd9cbbbebb221ae938d065b93ebb26efeda40b220aeed7a332a94da7129cdc",
        "reason": "reviewed_legacy_wrong_subject: A collection of verified statements about the meaning of the term 'ancient'"
    },
    "capital-cities": {
        "lead_sha256": "73723bf925e126992d74fe2b242f7ef4913b44f58385f0fb18764c5a0ff430bb",
        "reason": "reviewed_legacy_evidence_failure: The provided evidence does not contain specific information about capital cities as primary administrative seats of government or their symbolic significance."
    },
    "chamonix-france": {
        "lead_sha256": "ae4db66d3c13c622ed4d8c0c7515c96cceac78e6591760892e8a95cb2fdda8de",
        "reason": "reviewed_legacy_evidence_failure: confirm that none of them mention Chamonix"
    },
    "chester-cheshire": {
        "lead_sha256": "c17a9dea0c0fa0ed813013443d6674bc3aecc1bd8cbe0c21c283546a2772bdb8",
        "reason": "reviewed_legacy_evidence_failure: the following points reflect the lack of Chester‑specific information"
    },
    "cotswold-way": {
        "lead_sha256": "96c11216ae56b8988e1ba527a0fa0a08fe1d09467228431a809b5c0c065b05da",
        "reason": "reviewed_legacy_trigger_subject_substitution: the long dash symbol and the English word long",
        "trigger_query": "Long-distance walking trail"
    },
    "cotswolds-area-of-outstanding-natural-beauty": {
        "lead_sha256": "78affbd5c4c78954b45ab61960b890a08667a6bf427e94a51f9eee912680e3a3",
        "reason": "reviewed_legacy_trigger_subject_substitution: This article explains the word \"designated\"",
        "trigger_query": "Designated landscape in England"
    },
    "country": {
        "lead_sha256": "57290dae9d5df1aaa2617ff4a28c830fc57833eba984e30647505d7271205ff8",
        "reason": "reviewed_legacy_evidence_failure: each item notes the absence of particular information about England within the evidence"
    },
    "coventry-archives-covid-city-council": {
        "lead_sha256": "2316b43b689f0e9db3369f33acc898807d6b723172325101e5247df060efaa65",
        "reason": "reviewed_legacy_trigger_subject_substitution: construction estimating platforms in the UK",
        "trigger_query": "Municipal records office"
    },
    "coventry-transport-museum": {
        "lead_sha256": "4fb4bebecb9451c5adca1153e1434cc2e1fafefcedffbab2f967d1ddef95d197",
        "reason": "reviewed_legacy_evidence_failure: contains no direct references to the museum itself"
    },
    "cumbria": {
        "lead_sha256": "b0c64e0ca03e916c274546cbff2b1436195c810958cc0b3e74c9401d22bee7cb",
        "reason": "reviewed_legacy_evidence_failure: The supplied evidence does not contain any specific information about Cumbria, so no verifiable claims can be made."
    },
    "delhi-population": {
        "lead_sha256": "24c14efa41135e3b33884386468244e2c34c9e381c08e30d7fff071a6fb68e3b",
        "reason": "reviewed_legacy_wrong_subject: This explainer outlines the meaning of demographic terms and presents key United Kingdom population statistics drawn from authoritative sources."
    },
    "design-museum-london": {
        "lead_sha256": "6bc1b3bd144df8d23d2f0e8a1f2cde33ebd9dfd480279b5edbeb46d8622216d2",
        "reason": "reviewed_legacy_evidence_failure: present verifiable claims about the absence of Design Museum‑related content"
    },
    "diana-memorial-island-althorp": {
        "lead_sha256": "29a402672a292920d4efee5ebfaf3c210afacf3b03f692248b6cf60a5ec8c131",
        "reason": "reviewed_legacy_wrong_subject: An overview of Snapchat’s Cameos feature"
    },
    "dundee-mcmanus": {
        "lead_sha256": "cfa1999a840590b49b4d865a194bc6a64ab1c777d078248774d640ce154daeed",
        "reason": "reviewed_legacy_wrong_subject: This article explores the origins, frequency, pronunciation, syntactic flexibility, and pragmatic functions of 'the'"
    },
    "dundee-mills-observatory": {
        "lead_sha256": "3e4620ef2fbe31378ac85ab45a9595df92b9565c8ba6fc57ebd11ca7de4acc7c",
        "reason": "reviewed_legacy_evidence_failure: no substantive claims can be made about Mills Observatory based solely on the supplied evidence"
    },
    "erechtheion": {
        "lead_sha256": "718bf82f154792be7cebfa770a9cca35a9498cbb0ef5802d0fc1e2a0f190f99d",
        "reason": "reviewed_legacy_wrong_subject: This explainer covers practical tips for Microsoft Office applications"
    },
    "fira-santorini": {
        "lead_sha256": "1c5f68de254c703d4900aae225ede619249df36aca8e3249879565161c739dfc",
        "reason": "reviewed_legacy_evidence_failure: All documents relate to installing or using classic Outlook on Windows"
    },
    "firth-of-forth": {
        "lead_sha256": "4dc9d07a5661a82e336914ee491723de7dbf72ca0c719bef3e0c7a74b394e68f",
        "reason": "reviewed_legacy_evidence_failure: The evidence provided here consists solely of CAD‑block repositories for spiral staircases"
    },
    "giondistrict": {
        "lead_sha256": "d5cec94a1ddfe5cc225216c8401164ccb9c9b97cfc050c4c85dffca2c8c0800e",
        "reason": "reviewed_legacy_evidence_failure: The evidence provided relates to several St Columba’s schools and their term dates pages"
    },
    "glastonbury-festival": {
        "lead_sha256": "866e85bffb3e75fa9a5ad9d7607f4de72ee2b55d22dd0dbb237cf6706784d5e3",
        "reason": "reviewed_legacy_wrong_subject: Key facts about Facebook account security, friend management, and platform features drawn from user support forums and technology news sources."
    },
    "great-lakes-pfas": {
        "lead_sha256": "d1170f21cfd1cf1125ad8b1d2f30e11c19427f89ef3af7711bbb0205448f6b5e",
        "reason": "reviewed_legacy_trigger_subject_substitution: The Lake District offers a diverse range of accommodation",
        "trigger_query": "freshwater-contamination"
    },
    "greater-london": {
        "lead_sha256": "49253141ba2355fbb37d90363f6936b12db6ab29e73b5b21216dcd33eebbe5b2",
        "reason": "reviewed_legacy_evidence_failure: All six sources are Microsoft Q&A pages concerning technical support topics"
    },
    "hastings-battlefield-east-sussex": {
        "lead_sha256": "999c597c0d100198a422fd24a1760a263d59853073affa2f6223ce15ad74d34f",
        "reason": "reviewed_legacy_wrong_subject: The Battlefield franchise is a long-running series of military first-person shooters"
    },
    "hawaiian-islands": {
        "lead_sha256": "de07d3094355d96e6c4a45a96f08affc9d78033247bee8c38212f9f2d0ddd2cf",
        "reason": "reviewed_legacy_wrong_subject: a look at the Archipelago gaming randomizer"
    },
    "heaton-park": {
        "lead_sha256": "9a9630857617ec8e9ca8ce555d10b1fe786e8589d7f22695562b530272af93f2",
        "reason": "reviewed_legacy_evidence_failure: The following items outline the specific aspects of Heaton Park that are absent from the supplied sources"
    },
    "herbert-art-gallery-museum": {
        "lead_sha256": "555cd9e41927601ad0c39dd4b9aa8b419aa26d4bdf612fcd62470dd7fcabe5ea",
        "reason": "reviewed_legacy_evidence_failure: none mention the Herbert Art Gallery & Museum, so no verifiable facts about it can be drawn"
    },
    "hindu-kush-afghanistan": {
        "lead_sha256": "0d0298f1ea5525f5562acc49ec273b76310e73f22063c1cb9b45f8d655fb3be4",
        "reason": "reviewed_legacy_evidence_failure: Consequently, the only accurate statements that can be made are that the sources lack any data on these subjects"
    },
    "history": {
        "lead_sha256": "0ddaa1fd78a96fc6525d40f1bfccdad84985aa39142a3d6e31fe34ac433ebaee",
        "reason": "reviewed_legacy_wrong_subject: the available evidence focuses on Microsoft account sign‑in procedures"
    },
    "inkarail-trail-peru": {
        "lead_sha256": "d16733cd5a2afc35b6492551a0d78ec376f1c664cc7563f3c5629b3dc2771d6a",
        "reason": "reviewed_legacy_wrong_subject: the supplied evidence concerns Trek bicycles"
    },
    "isambard-kingdom-brunel-bristol": {
        "lead_sha256": "1f2237d52d2483becee18f4ea7fc40e24eb964e3b5dd78f60a6a2f9858dc3381",
        "reason": "reviewed_legacy_wrong_subject: overview of what an engineer is, the main pathways into the profession, typical duties, major disciplines and the professional registration landscape in the UK."
    },
    "izmir": {
        "lead_sha256": "3d76981b5537c704168b0f4b209b043bfbbe0d4ca479a69b41c3cd0ec4540fbd",
        "reason": "reviewed_legacy_evidence_failure: each item notes the absence of any reference to the city"
    },
    "jakarta-chinatown": {
        "lead_sha256": "d578dd36c44dfa02cab5f10da979015f3bf7fe6f4b030f0dab9c72698c4c0220",
        "reason": "reviewed_legacy_evidence_failure: the explicit statement that no Jakarta‑specific information is present in the supplied material"
    },
    "kabul-city-afghanistan": {
        "lead_sha256": "91543fa2a0ac7e4ab74d212ff75b81105e09ded35a3c70159f3e9b5d011b46a0",
        "reason": "reviewed_legacy_evidence_failure: Because the sources concern Dundee, Scotland, they contain no direct facts about Kabul"
    },
    "kabul-silk-road-heritage": {
        "lead_sha256": "e89ca49a63d6eba0ac77f44282c89e06a462bb2c58b24db50360a9afc6bb8b6c",
        "reason": "reviewed_legacy_wrong_subject: verified facts about Castleford’s early medieval and later heritage"
    },
    "keswick-town": {
        "lead_sha256": "0c6015b6bccf50a6b56408b4c7e78142fdeca2b351e5f5a75b8d2c8c42596f46",
        "reason": "reviewed_legacy_evidence_failure: None of these sources contain any reference to Keswick, its geography, history or tourism."
    },
    "kinkaku-ji": {
        "lead_sha256": "84022bf43c4803cd9b3d3a64b1bbe9c2a0165bcc824141172afe07263a1570d9",
        "reason": "reviewed_legacy_trigger_subject_substitution: Stechford is a historic suburban district in east Birmingham",
        "trigger_query": "Buddhist temple in Kyoto"
    },
    "kinkaku-ji-temple": {
        "lead_sha256": "d3a5a12a07ca7c90b3bd32d132d7bed15e8d2eadda216274e021af4b8355c651",
        "reason": "reviewed_legacy_evidence_failure: This makes it impossible to generate accurate 'What10Things' explainers about the temple itself from the given sources."
    },
    "kotatua-jakarta": {
        "lead_sha256": "a2a2cdfe4cf6b2a1de15028202da331e12a4a35893d52580291676cbce633345",
        "reason": "reviewed_legacy_evidence_failure: Each item notes a specific aspect of Kota Tua that is absent from the evidence"
    },
    "lakedistrict-national-park": {
        "lead_sha256": "cf7f57781dec901a496c639cda5fee3c9694cb4ae0fe8788cf4f363fa078cc25",
        "reason": "reviewed_legacy_wrong_subject: This explainer examines the definition, usage, synonyms, antonyms, and legal implications of the term 'protected'"
    },
    "liverpool-street-station": {
        "lead_sha256": "cd9e28e9e2f363c0e04b8fdab27250c24960211fb489a69813dd066c07b48d74",
        "reason": "reviewed_legacy_wrong_subject: detail property‑data and estate‑agency services offered by Landmark Information Group"
    },
    "livingstone-island": {
        "lead_sha256": "ffe47d8734346db3477dea9f436ef4c80ef5b69989072fcb18481e30bd6285a1",
        "reason": "reviewed_legacy_trigger_subject_substitution: The UK property market is dominated by several leading online portals",
        "trigger_query": "Livingstone Island"
    },
    "local-dining-establishments": {
        "lead_sha256": "dc39656449bebbad8f90a36b28846a5a93c2e53ccb22ed6a4e4e1792da44d7ce",
        "reason": "reviewed_legacy_wrong_subject: While the candidate references Bradford, the provided evidence exclusively covers London's food and drink scene."
    },
    "london-museum-docklands": {
        "lead_sha256": "a6508686221648bc6c3986a48ba17781752a917d13522786fb8f8a2ffda83b14",
        "reason": "reviewed_legacy_trigger_subject_substitution: An exploration of waterfront venues and residential developments",
        "trigger_query": "Waterfront museum complex"
    },
    "london-water-supply": {
        "lead_sha256": "1290922129cee8e167d1f889223ead8164ef771d3e4e855151c8c2bde86cd7b7",
        "reason": "reviewed_legacy_wrong_subject: Because no source references London, the River Thames, or Thames Water, the items below reflect what the evidence actually supports"
    },
    "long-distance-trails-uk": {
        "lead_sha256": "5d82e32c1e0e7e639943617cec4ecb9838579391bb399d4298210e82b611b04c",
        "reason": "reviewed_legacy_evidence_failure: The supplied evidence does not contain any information about the Pennine Way or other UK long-distance footpaths"
    },
    "monte-bianco-italy-france": {
        "lead_sha256": "3db6401db74846a2f02d9f59a47558021931eab5c2f5dea38305842a9b32f0b3",
        "reason": "reviewed_legacy_evidence_failure: the following items describe what the evidence lacks regarding Mont Blanc"
    },
    "mosi-oa-tunya-national-park": {
        "lead_sha256": "43e7051a62d11c1cc13270523d6e06b4deeec3a954d933f8f3b397a2984a544f",
        "reason": "reviewed_legacy_trigger_subject_substitution: An overview of OpenClip for Safari",
        "trigger_query": "Mosi-oa-Tunya National Park"
    },
    "national-capitals": {
        "lead_sha256": "20492ff37c7b61155a6aa83fba8da5c5f9ffe9c393e84eebf2773dd47bc9d0e3",
        "reason": "reviewed_legacy_evidence_failure: While the candidate title references national capitals, the actual evidence does not contain information on this topic."
    },
    "national-monument-jakarta": {
        "lead_sha256": "378ae958261eeb9d69f1a7c82876d9a66aa04ac519e2caed959597abfa62b3b8",
        "reason": "reviewed_legacy_evidence_failure: None of the supplied sources mention the National Monument (Monas)"
    },
    "nazca-lines": {
        "lead_sha256": "864ac0ad6aab9e393a839ead0a33205f2ae75bab9ed6cdb06324938a94f061a3",
        "reason": "reviewed_legacy_evidence_failure: None of these profiles contain any information about the Nazca Lines"
    },
    "nicholas-winton": {
        "lead_sha256": "fdd1885ac2927c85cf8b7b8c07c1bbc3f7d7fdde3573d3cd0a1eae32300be8a9",
        "reason": "reviewed_legacy_evidence_failure: The following items highlight that the provided source material contains no reference to Nicholas Winton or his role in the Kindertransport."
    },
    "orbit-tower-london": {
        "lead_sha256": "f59ce76aa62a89589c5f1865a52c71d5beafaafed89d56266feb31213019debd",
        "reason": "reviewed_legacy_evidence_failure: the explainer notes the absence of information in the provided sources"
    },
    "persian-garden-design": {
        "lead_sha256": "b46f194196159e642b82119eac74fb59ee5f5bc0506ccc835f3b6340905bebc4",
        "reason": "reviewed_legacy_evidence_failure: The following items summarise what each source covers and what it omits regarding Persian garden design"
    },
    "prague": {
        "lead_sha256": "1ce6ab3beacd734ab2a77c88644c825e470c1e0ab97803a64eedf84cb5b96476",
        "reason": "reviewed_legacy_wrong_subject: The supplied sources describe the City of London’s governance, status and visitor offer, and the Mayor of London’s administration."
    },
    "pulteney-bridge-bath": {
        "lead_sha256": "da8a1c585f2227fd22b09acfc5f2d69ea290bd09dd81d2fab1a0d7a3fdc9bee9",
        "reason": "reviewed_legacy_evidence_failure: The items below therefore note absent details that the evidence does not mention"
    },
    "queen-elizabeth-olympic-park-london": {
        "lead_sha256": "64afa8f3bf15e21e8f584ff14febd484823ae34f0724970783cbab4d0dc7d2a9",
        "reason": "reviewed_legacy_wrong_subject: They cover the number and type of play facilities managed by Cramlington Town Council"
    },
    "royal-crescent-bath": {
        "lead_sha256": "533f9800204445361934879955bafefcf14a1be6434838d6b6c9016f56ea7b6d",
        "reason": "reviewed_legacy_evidence_failure: note where information about this landmark is missing"
    },
    "royal-mile-edinburgh": {
        "lead_sha256": "cb4c7878dddf3a4efa525e4ba15ecc5a9d1d6ed843d65e7f3a84368bbfd93edb",
        "reason": "reviewed_legacy_wrong_subject: it focuses exclusively on African textiles and loom technologies"
    },
    "royal-shakespeare-theatre": {
        "lead_sha256": "4e687d10807100adb06842ad930c6e56f632c204545b5ac44fb08fdc05e8bf28",
        "reason": "reviewed_legacy_evidence_failure: No information about the Royal Shakespeare Theatre is present in the supplied evidence."
    },
    "sacred-valley-peru": {
        "lead_sha256": "841f41e1853bf532f290fabb16d7f20b6fe0ef3c8fe41b5845b3cc1efbf3e6d3",
        "reason": "reviewed_legacy_evidence_failure: the following items describe what the evidence does not mention regarding various aspects of the valley"
    },
    "saint-petersburg-russia": {
        "lead_sha256": "ab3d6271669bfd92354f778a51d6ca03abb502d8c6ef51458b1921f05dce8dd9",
        "reason": "reviewed_legacy_evidence_failure: The following items clarify which aspects of Saint Petersburg are absent from the given material"
    },
    "scaffell-pike": {
        "lead_sha256": "ed664bb9b77874ded0774651336e2427472eba50680e83bf82ef1a22144a9092",
        "reason": "reviewed_legacy_trigger_subject_substitution: the different types of heating oil used in UK homes",
        "trigger_query": "mountain"
    },
    "senlac-hill-battlefield-east-sussex": {
        "lead_sha256": "1f4f34ecddb79598994411b3242903e8cc056efb3b5343778d8378d856cef3ba",
        "reason": "reviewed_legacy_evidence_failure: none of the provided sources mention Senlac Hill Battlefield"
    },
    "seven-oaks-park-cramlington": {
        "lead_sha256": "c11ba36c848222466b8e9402019201878074c0702451670ebd149f8a47a0a88e",
        "reason": "reviewed_legacy_evidence_failure: each item documents the absence of specific information across the sources"
    },
    "shikinen-sengu-ritual": {
        "lead_sha256": "6d5fb32cd2f8645cea3f96e9b56aa609ec1f03fc2501cca75300e1dd8f8ea5da",
        "reason": "reviewed_legacy_wrong_subject: No source material about Shikinen Sengu is present in the evidence set."
    },
    "shinto": {
        "lead_sha256": "6a1278deccf13963b63222f6c6fb0e076f166352db265eb8bcc3bb97961ada27",
        "reason": "reviewed_legacy_trigger_subject_substitution: covering technology platforms, gaming communities, music, and academic practices",
        "trigger_query": "religion"
    },
    "sir-david-attenborough-biography": {
        "lead_sha256": "b65fe10dcc9ad989e3a332ebebd39d773b8c380cce2a2b9db2b4fc71ba7ce224",
        "reason": "reviewed_legacy_evidence_failure: each entry states that the supplied evidence lacks details"
    },
    "skanderbeg-square-tirana": {
        "lead_sha256": "5ed10194f13e919ec74c2232c9769a78df15be299aa5131a6c7d8313f76f84d1",
        "reason": "reviewed_legacy_wrong_subject: This explainer examines the meaning and usage of the term 'public'"
    },
    "snowdonia-eryri": {
        "lead_sha256": "f41ae854dbd09ff1b1735f00132c89602bc0b6c6053775730b6637970c8b5bc7",
        "reason": "reviewed_legacy_wrong_subject: The supplied evidence details several UK-wide national services rather than Eryri National Park."
    },
    "south-kensington": {
        "lead_sha256": "ba3668fc1cecf7926808c87628a1f436b32ad341196731dffb47c39befd2efa4",
        "reason": "reviewed_legacy_wrong_subject: The following items clarify what ‘cultural’ means in English"
    },
    "ss-great-britain-bristol": {
        "lead_sha256": "e49199d0a90e9cf5f5513b624ae30c0808b2e6134641d1c8774e591314385cb5",
        "reason": "reviewed_legacy_trigger_subject_substitution: An overview of Walsall’s origins, medieval development and industrial growth",
        "trigger_query": "historic_ship"
    },
    "st-machar-cathedral": {
        "lead_sha256": "9ce9417703ffb4541d64856c008f0996a3aed21d9fb22469090317631d20e748",
        "reason": "reviewed_legacy_trigger_subject_substitution: how the ordinal number 12th is formed, used, and spelled",
        "trigger_query": "12th-century cathedral in Old Aberdeen"
    },
    "st-machars-cathedral": {
        "lead_sha256": "f0ae508b5dc710d978d711422b66fee96aafe37da2bd99af8aac4a650c95ec78",
        "reason": "reviewed_legacy_trigger_subject_substitution: the ordinal number 12th (twelfth)",
        "trigger_query": "12th‑century cathedral still in use"
    },
    "st-marks-basilica-venice": {
        "lead_sha256": "a93aa2b3314876b8eb1a6204a77be3e1472d7b2cc7beb090522b5d6301b8e68d",
        "reason": "reviewed_legacy_evidence_failure: the supplied material, which pertains to a pub in West Sussex"
    },
    "thames-head-kemble": {
        "lead_sha256": "932d73302a1ea6fc760b87e396d7d1db8436338a5fea64d295f2b73a943a5c85",
        "reason": "reviewed_legacy_evidence_failure: None of those sources contain any direct information about Thames Head, Kemble; each item therefore notes a specific aspect that is absent from the evidence."
    },
    "the-circus-bath": {
        "lead_sha256": "148de78d8d6b245ec1d7274e972c22f2efaff0f371af839931c6d82b3c1f9fab",
        "reason": "reviewed_legacy_wrong_subject: This explainer presents 14 evidence‑based facts about Facebook account management, drawn from the supplied sources."
    },
    "the-commandery": {
        "lead_sha256": "8930c62a03515d277c360cbb6006ecd59ba8063cad6343f0333568bcaba684bc",
        "reason": "reviewed_legacy_evidence_failure: the only facts we can assert with confidence are what the sources do *not* tell us about the property"
    },
    "titanic-belfast": {
        "lead_sha256": "7e47edcb9cfedf8ffa1eafc6a66d4a19b066c7d9527079eb2f299585beb29d65",
        "reason": "reviewed_legacy_evidence_failure: the following items describe what the evidence lacks regarding this attraction"
    },
    "tokyo-population": {
        "lead_sha256": "a8ccd506d55992ec23503630202d9e6884dbc21832336f14053f75d88496e5c4",
        "reason": "reviewed_legacy_evidence_failure: The current evidence set provides only general definitions of demographic terms, without numeric data for Tokyo."
    },
    "tower-of-london": {
        "lead_sha256": "5a17869ab652652882143ef4d88fb0e878a5145639449d21ff2363a67d0cb6c2",
        "reason": "reviewed_legacy_evidence_failure: The following items document this absence of supporting evidence"
    },
    "trafalgar-square-london": {
        "lead_sha256": "dda47bbc5858d3bc525dcdcb326ff69373ac3f61ef5ebe6758c550f0354575d7",
        "reason": "reviewed_legacy_evidence_failure: The following points highlight what the evidence does not cover regarding this London public space"
    },
    "trans-siberian-railway": {
        "lead_sha256": "14f3bbfe84a0b0b4e7ff70d0fde3a09d18f7c62e38a614b60069de091248505d",
        "reason": "reviewed_legacy_wrong_subject: An overview of the ChargePlace Scotland electric‑vehicle charging network"
    },
    "travel": {
        "lead_sha256": "15175910cb99e10f136b624b1f6cd43d402aa13b4b1e52e3a9509a952c177860",
        "reason": "reviewed_legacy_wrong_subject: This explainer looks at the meaning of activity"
    },
    "uk-income-tax-rates": {
        "lead_sha256": "90680acfa03bf73edbd55ae69458c8c76a6d0a65bc757db1ea87566fdfa33ff1",
        "reason": "reviewed_legacy_evidence_failure: they focus exclusively on bed and breakfast accommodations"
    },
    "ulster-museum": {
        "lead_sha256": "168823c42566f195e629628c492f2e627370fd4d832e9a769a5550df4fb6da07",
        "reason": "reviewed_legacy_evidence_failure: The following items each state this absence in slightly different wording"
    },
    "ulster-museum-belfast": {
        "lead_sha256": "36fac8001da9c0009cf1651868a772adb56e2c90ebd1b001cd730288e033fcf7",
        "reason": "reviewed_legacy_wrong_subject: the available evidence concerns the Canadian writer Liz Harmer and her affiliations"
    },
    "unesco-world-heritage-afghanistan": {
        "lead_sha256": "dedb2c47df042f85f9e38401c6d82abc3205448ea259687e2c2f70c02fec31e0",
        "reason": "reviewed_legacy_evidence_failure: None of the sources reference Afghanistan or its World Heritage properties"
    },
    "unesco-world-heritage-algiers": {
        "lead_sha256": "4bfb4a9d0e878aff5cc7d586f6c7148a6b8c877f8a46665326aa85e65f578265",
        "reason": "reviewed_legacy_evidence_failure: the following items reflect the limits of the available data rather than substantive facts about the sites themselves"
    },
    "university": {
        "lead_sha256": "79033652bbeb090a259aaa67973831f962cb7d7032674fb344212b4185943ee8",
        "reason": "reviewed_legacy_trigger_subject_substitution: covering trivia games, career platforms, language definitions, music history, and interactive comparison tools",
        "trigger_query": "Higher Education Institution"
    },
    "valley-park-cramlington": {
        "lead_sha256": "06ed13b0d0afdb7bb1472b8420328037a872d74ef4b064ff1adaee3a245fd9e5",
        "reason": "reviewed_legacy_wrong_subject: Manchester’s parks and gardens offer a range of experiences"
    },
    "victoria-and-albert-museum": {
        "lead_sha256": "796da1af963eed0422cf322ad3ea1754d0f1669221207f6dc564a0f3c11783e5",
        "reason": "reviewed_legacy_wrong_subject: A concise guide to Belfast's key museums and heritage sites"
    },
    "wallace-monument": {
        "lead_sha256": "84e1f696203a73e63ccd4c4b51656202e777abde5413145a0b576260d867e239",
        "reason": "reviewed_legacy_wrong_subject: An overview of what constitutes a monument, with examples from the Monument in London and the Monument Bank brand"
    },
    "westminster-abbey": {
        "lead_sha256": "a288e7ea8c8db209526790a04f53b4a1db041fbfdd531dc6c12c37688757999d",
        "reason": "reviewed_legacy_evidence_failure: The following fourteen items each state that none of the provided source materials mention Westminster Abbey"
    },
    "white-cliffs-of-dover": {
        "lead_sha256": "ad47eaa15ce6822e9bb0c68ad1d1b3cddcb5a3fdcf1ff67cc4224b2d48683c65",
        "reason": "reviewed_legacy_wrong_subject: A collection of factual explanations about the term 'natural' drawn exclusively from dictionary and journal sources provided in the evidence."
    },
    "wordsworth-museum-grasmere": {
        "lead_sha256": "b3279f75e8e38cb8646fd8d9a061c3a1663d66011f46468a8a19aa52adaf39bd",
        "reason": "reviewed_legacy_evidence_failure: The supplied evidence does not contain information about Wordsworth Museum, Grasmere."
    },
    "zurich-switzerland": {
        "lead_sha256": "c136e06285d01ade7c50c466a01a17b82bfbac498fb52c0b40e556aca72f4436",
        "reason": "reviewed_legacy_wrong_subject: York is a historic cathedral city in northern England"
    }
}


def reviewed_legacy_issue(payload: dict[str, Any]) -> str | None:
    record = REVIEWED_LEGACY_HOLDS.get(str(payload.get("slug") or ""))
    if record is None:
        return None
    lead = {key: str(payload.get(key) or "") for key in ("title", "summary", "intro")}
    digest = hashlib.sha256(json.dumps(lead, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if digest != record["lead_sha256"]:
        return None
    if "trigger_query" in record:
        trigger = payload.get("trigger")
        if not isinstance(trigger, dict) or trigger.get("query") != record["trigger_query"]:
            return None
    return record["reason"]
