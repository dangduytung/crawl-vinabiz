class Company:
    # WEB CRAWL
    url = ''
    
    # THÔNG TIN ĐĂNG KÝ DOANH NGHIỆP
    official_name = ''
    trading_name = ''
    bussiness_code = ''
    date_of_license = ''
    administration_tax_agency = ''
    start_working_date = ''
    status = ''

    # THÔNG TIN LIÊN HỆ
    address = ''
    phone = ''
    fax = ''
    email = ''
    web = ''
    representative = ''
    representative_phone = ''
    representative_address = ''
    director = ''
    director_phone = ''
    director_address = ''
    accountant = ''
    accountant_phone = ''
    accountant_address = ''

    # THÔNG TIN NGÀNH NGHỀ, LĨNH VỰC HOẠT ĐỘNG
    main_job = ''
    economic_field = ''
    economic_type = ''
    organization_type = ''
    chapter_level = ''
    economic_type_child = ''

    def __repr__(self):
        return str(self.__dict__)
