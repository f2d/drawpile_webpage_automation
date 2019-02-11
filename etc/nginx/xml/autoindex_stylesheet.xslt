<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<!-- Variables: *- - - - - - - - - - - - - - - - - - - - - - - - - - - - - !-->

<xsl:variable name="sort_data_type">
	<xsl:choose>
		<xsl:when test="$sort_by = 'size'">number</xsl:when>
		<xsl:otherwise>text</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_index">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Содержание</xsl:when>
		<xsl:otherwise>Index of</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_empty">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Пусто</xsl:when>
		<xsl:otherwise>Empty</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_name">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Имя</xsl:when>
		<xsl:otherwise>Name</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_time">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Дата</xsl:when>
		<xsl:otherwise>Date</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_size">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Размер</xsl:when>
		<xsl:otherwise>Size</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_size_b">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">байт</xsl:when>
		<xsl:otherwise>bytes</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_size_k">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">К</xsl:when>
		<xsl:otherwise>K</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_size_m">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">М</xsl:when>
		<xsl:otherwise>M</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="lang_size_g">
	<xsl:choose>
		<xsl:when test="$lang = 'ru'">Г</xsl:when>
		<xsl:otherwise>G</xsl:otherwise>
	</xsl:choose>
</xsl:variable>

<xsl:variable name="show_in_k"><xsl:number value="1000" /></xsl:variable>
<xsl:variable name="show_in_m"><xsl:number value="1000000" /></xsl:variable>
<xsl:variable name="show_in_g"><xsl:number value="1000000000" /></xsl:variable>

<xsl:variable name="bytes_in_k"><xsl:number value="1024" /></xsl:variable>
<xsl:variable name="bytes_in_m"><xsl:number value="1048576" /></xsl:variable>
<xsl:variable name="bytes_in_g"><xsl:number value="1073741824" /></xsl:variable>

<!-- Functions: *- - - - - - - - - - - - - - - - - - - - - - - - - - - - - !-->

<!-- https://stackoverflow.com/a/3067130 -->
<xsl:template name="string-replace-all">
	<xsl:param name="text" />
	<xsl:param name="replace" />
	<xsl:param name="by" />
	<xsl:choose>
		<xsl:when test="$text = '' or $replace = '' or not($replace)" >
			<!-- Prevent this routine from hanging -->
			<xsl:value-of select="$text" />
		</xsl:when>
		<xsl:when test="contains($text, $replace)">
			<xsl:value-of select="substring-before($text, $replace)" />
			<xsl:value-of select="$by" />
			<xsl:call-template name="string-replace-all">
				<xsl:with-param name="text" select="substring-after($text, $replace)" />
				<xsl:with-param name="replace" select="$replace" />
				<xsl:with-param name="by" select="$by" />
			</xsl:call-template>
		</xsl:when>
		<xsl:otherwise>
			<xsl:value-of select="$text" />
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>

<xsl:template name="get-url-escaped-name">
	<xsl:call-template name="string-replace-all">
		<xsl:with-param name="text" select="normalize-space(.)" />
		<xsl:with-param name="replace" select="'#'" />
		<xsl:with-param name="by" select="'%23'" />
	</xsl:call-template>
</xsl:template>

<xsl:template name="get-formatted-size-text">
	<xsl:param name="num" />
	<xsl:param name="div" />
	<xsl:param name="text" />

	<xsl:value-of select="format-number(($num div $div), '0.00')" />
	<xsl:text> </xsl:text>
	<xsl:value-of select="$text" />
</xsl:template>

<xsl:template name="get-formatted-size">
	<xsl:param name="size" />

	<xsl:if test="string-length($size) &gt; 0">
		<xsl:variable name="bytes">
			<xsl:number value="number($size)" />
		</xsl:variable>

		<xsl:choose>
			<xsl:when test="$bytes &gt;= $show_in_g">
				<xsl:call-template name="get-formatted-size-text">
					<xsl:with-param name="num" select="$size" />
					<xsl:with-param name="div" select="$bytes_in_g" />
					<xsl:with-param name="text" select="$lang_size_g" />
				</xsl:call-template>
			</xsl:when>

			<xsl:when test="$bytes &gt;= $show_in_m">
				<xsl:call-template name="get-formatted-size-text">
					<xsl:with-param name="num" select="$size" />
					<xsl:with-param name="div" select="$bytes_in_m" />
					<xsl:with-param name="text" select="$lang_size_m" />
				</xsl:call-template>
			</xsl:when>

			<xsl:when test="$bytes &gt;= $show_in_k">
				<xsl:call-template name="get-formatted-size-text">
					<xsl:with-param name="num" select="$size" />
					<xsl:with-param name="div" select="$bytes_in_k" />
					<xsl:with-param name="text" select="$lang_size_k" />
				</xsl:call-template>
			</xsl:when>

			<xsl:otherwise>
				<xsl:value-of select="$size" />
			</xsl:otherwise>
		</xsl:choose>
	</xsl:if>
</xsl:template>

<xsl:template name="column">
	<xsl:param name="title" />
	<xsl:param name="by" />

	<th>
		<xsl:value-of select="$title" />
		<xsl:text> </xsl:text>
		<a href="?sort_by={$by}&amp;sort_order=ascending">▲</a>
		<xsl:text> </xsl:text>
		<a href="?sort_by={$by}&amp;sort_order=descending">▼</a>
	</th>
</xsl:template>

<xsl:template name="directory">
	<tr>
		<xsl:variable name="url-escaped-name">
			<xsl:call-template name="get-url-escaped-name" />
			<xsl:text>/</xsl:text>
		</xsl:variable>

		<xsl:variable name="name">
			<xsl:value-of select="normalize-space(.)" />
			<xsl:text>/</xsl:text>
		</xsl:variable>

		<td colspan="2"><a href="{$url-escaped-name}"><xsl:value-of select="$name" /></a></td>
		<td><time data-t="{@mtime}"><xsl:value-of select="@mtime" /></time></td>
	</tr>
</xsl:template>

<xsl:template name="file">
	<tr>
		<xsl:variable name="url-escaped-name">
			<xsl:call-template name="get-url-escaped-name" />
		</xsl:variable>

		<xsl:variable name="name">
			<xsl:value-of select="normalize-space(.)" />
		</xsl:variable>

		<xsl:variable name="name_length">
			<xsl:value-of select="string-length($name)" />
		</xsl:variable>

		<xsl:variable name="size_bytes">
			<xsl:value-of select="@size" />
			<xsl:text> </xsl:text>
			<xsl:value-of select="$lang_size_b" />
		</xsl:variable>

		<xsl:variable name="size_formatted">
			<xsl:call-template name="get-formatted-size">
				<xsl:with-param name="size" select="@size" />
			</xsl:call-template>
		</xsl:variable>

		<xsl:choose>
			<xsl:when test="$name_length > 5 and substring($name, $name_length - 5) = '.dprec'">
				<td><a href="{$url-escaped-name}" target="_blank" rel="nofollow"><xsl:value-of select="$name" /></a></td>
			</xsl:when>
			<xsl:otherwise>
				<td><a href="{$url-escaped-name}" target="_blank"><xsl:value-of select="$name" /></a></td>
			</xsl:otherwise>
		</xsl:choose>

		<td title="{$size_bytes}"><xsl:value-of select="$size_formatted" /></td>
		<td><time data-t="{@mtime}"><xsl:value-of select="@mtime" /></time></td>
	</tr>
</xsl:template>

<!-- Transform: *- - - - - - - - - - - - - - - - - - - - - - - - - - - - - !-->

<xsl:template match="/">
	<html lang="{$lang}">
	<head>
		<meta charset="utf-8" />
		<title>
			<xsl:value-of select="$lang_index" />
			<xsl:text> </xsl:text>
			<xsl:value-of select="$path_here" />
		</title>
		<link rel="stylesheet" type="text/css" href="/index.css" />
		<link rel="shortcut icon" type="image/png" href="/d.png" />
		<script src="/index.js"></script>
	</head>
	<body class="outside">
		<table>
		<tr>
		<td>
		<div class="inside">
			<h3>
				<xsl:value-of select="$lang_index" />
				<xsl:text> </xsl:text>
				<span id="path">
					<xsl:if test="string-length($path_back) &gt; 0">
						<a href="{$path_back}">
							<xsl:value-of select="$path_back" />
						</a>
					</xsl:if>
					<xsl:value-of select="$name_here" />
					<xsl:text>/</xsl:text>
				</span>
				<xsl:text>:</xsl:text>
			</h3>

			<xsl:choose>
				<xsl:when test="count(list/*) = 0">
					<xsl:value-of select="$lang_empty" />
					<xsl:text>.</xsl:text>
				</xsl:when>
				<xsl:otherwise>
					<table class="simple-rows-table">
						<thead>
							<xsl:call-template name="column">
								<xsl:with-param name="title">
									<xsl:value-of select="$lang_name" />
								</xsl:with-param>
								<xsl:with-param name="by">name</xsl:with-param>
							</xsl:call-template>

							<xsl:call-template name="column">
								<xsl:with-param name="title">
									<xsl:value-of select="$lang_size" />
								</xsl:with-param>
								<xsl:with-param name="by">size</xsl:with-param>
							</xsl:call-template>

							<xsl:call-template name="column">
								<xsl:with-param name="title">
									<xsl:value-of select="$lang_time" />
								</xsl:with-param>
								<xsl:with-param name="by">mtime</xsl:with-param>
							</xsl:call-template>
						</thead>

						<tbody>
							<xsl:for-each select="list/directory">
								<xsl:sort select="@*[name()=$sort_by]" data-type="{$sort_data_type}" order="{$sort_order}" />
								<xsl:sort select="." data-type="text" order="{$sort_order}" />
								<xsl:call-template name="directory" />
							</xsl:for-each>
							
							<xsl:for-each select="list/file">
								<xsl:sort select="@*[name()=$sort_by]" data-type="{$sort_data_type}" order="{$sort_order}" />
								<xsl:sort select="." data-type="text" order="{$sort_order}" />
								<xsl:call-template name="file" />
							</xsl:for-each>
						</tbody>
					</table>
				</xsl:otherwise>
			</xsl:choose>
		</div>
		</td>
		</tr>
		</table>
	</body>
	</html>
</xsl:template>

</xsl:stylesheet>
