import logging
import re
import time
import os

# Allow Django ORM operations in Scrapy's async context
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import scrapy
from django.db import IntegrityError
from django.utils.text import slugify

from crawler.models import Generic, Manufacturer
from medexbot.items import MedItem, GenericItem


class MedSpider(scrapy.Spider):
    name = "med"
    allowed_domains = ['medex.com.bd']
    start_urls = ['https://medex.com.bd/brands?page=1', 'https://medex.com.bd/brands?herbal=1&page=1']

    def clean_text(self, raw_html):
        """
        :param raw_html: this will take raw html code
        :return: text without html tags
        """
        cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        return re.sub(cleaner, '', raw_html)

    def parse(self, response, **kwargs):
        brand_links = response.css('a.brand-card::attr(href)').getall()
        yield from response.follow_all(brand_links, self.parse_med)

        pagination_links = response.css('a.page-link[rel="next"]::attr(href)').getall()
        yield from response.follow_all(pagination_links, self.parse)

    def parse_generic(self, response):
        item = GenericItem()

        generic_id_match = re.findall(r"generics/(\d+)", response.url)
        if not generic_id_match:
            return
        item['generic_id'] = int(generic_id_match[0])

        generic_name_val = response.css('h1.page-heading-1-l ::text').get()
        item['generic_name'] = generic_name_val.strip() if generic_name_val else "Unknown Generic"

        item['monograph_link'] = response.css('span.hidden-sm a::attr(href)').get()

        def get_description(element_id):
            sibling = response.xpath(f'//div[@id="{element_id}"]/following-sibling::div[1]')
            if sibling:
                val = sibling.get()
                return val.strip() if val else None
            return None

        item['indication_description'] = get_description('indications')
        item['therapeutic_class_description'] = get_description('drug_classes')
        item['pharmacology_description'] = get_description('mode_of_action')
        item['dosage_description'] = get_description('dosage')
        item['administration_description'] = get_description('administration')
        item['interaction_description'] = get_description('interaction')
        item['contraindications_description'] = get_description('contraindications')
        item['side_effects_description'] = get_description('side_effects')
        item['pregnancy_and_lactation_description'] = get_description('pregnancy_cat')
        item['precautions_description'] = get_description('precautions')
        item['pediatric_usage_description'] = get_description('pediatric_uses')
        item['overdose_effects_description'] = get_description('overdose_effects')
        item['duration_of_treatment_description'] = get_description('duration_of_treatment')
        item['reconstitution_description'] = get_description('reconstitution')
        item['storage_conditions_description'] = get_description('storage_conditions')

        item['slug'] = slugify(item['generic_name'] + '-' + str(item['generic_id']), allow_unicode=True)
        yield item

    def parse_med(self, response):
        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        item = MedItem()

        brand_id_match = re.findall(r"brands/(\d+)", response.url)
        if not brand_id_match:
            return
        item['brand_id'] = int(brand_id_match[0])

        brand_name_text = response.css('h1.page-heading-1-l::text').get()
        if not brand_name_text:
            brand_name_text = "".join(response.css('h1.page-heading-1-l *::text').getall())
        item['brand_name'] = brand_name_text.strip() if brand_name_text else "Unknown Brand"

        type_alt = response.css('h1.page-heading-1-l img::attr(alt)').get()
        item['type'] = 'herbal' if type_alt and type_alt.strip().lower() == 'herbal' else 'allopathic'

        item['dosage_form'] = extract_with_css('small.h1-subtitle::text')
        item['strength'] = extract_with_css('div[title="Strength"]::text')

        # manufacturer extraction
        manufacturer_link = extract_with_css('div[title="Manufactured by"] a::attr(href)')
        manufacturer_id_match = re.findall(r"companies/(\d+)", manufacturer_link) if manufacturer_link else []
        if manufacturer_id_match:
            manufacturer_id = int(manufacturer_id_match[0])
            manufacturer_name = extract_with_css('div[title="Manufactured by"] a::text')
            try:
                item['manufacturer'] = Manufacturer.objects.get(manufacturer_id=manufacturer_id)
            except Manufacturer.DoesNotExist:
                try:
                    item['manufacturer'] = Manufacturer.objects.create(
                        manufacturer_id=manufacturer_id,
                        manufacturer_name=manufacturer_name,
                        slug=slugify(manufacturer_name + '-' + str(manufacturer_id), allow_unicode=True)
                    )
                except IntegrityError as ie:
                    logging.info(ie)
                    item['manufacturer'] = None
        else:
            item['manufacturer'] = None

        package_container = ','.join(
            [re.sub(r'\s+', ' ', i).strip() for i in response.css('div.package-container::text').getall() if i.strip()]
        )
        pack_size_info = ','.join(
            [re.sub(r'\s+', ' ', i).strip() for i in response.css('span.pack-size-info::text').getall() if i.strip()]
        )

        item['package_container'] = package_container
        item['pack_size_info'] = pack_size_info

        item['slug'] = slugify(item['brand_name'] + ' ' + item['dosage_form'] + ' ' + item['strength'], allow_unicode=True)

        # generic extraction
        generic_link = extract_with_css('div[title="Generic Name"] a::attr(href)')
        generic_id_match = re.findall(r"generics/(\d+)", generic_link) if generic_link else []
        if generic_id_match:
            generic_id = int(generic_id_match[0])
            try:
                item['generic'] = Generic.objects.get(generic_id=generic_id)
            except Generic.DoesNotExist:
                # Save the generics id with medicines id to map them later
                with open('generic_id.txt', 'a') as f:
                    f.write(f"{item['brand_id']},{generic_id}\n")

                yield response.follow(generic_link, self.parse_generic)
                item['generic'] = None
            except IntegrityError as ie:
                logging.info(ie)
                item['generic'] = None
        else:
            item['generic'] = None

        yield item
