# coding=utf-8
from pydoc import visiblename
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import requests
import json
from tigacrafting.models import *
from tigaserver_app.models import Photo, Report, ReportResponse
import dateutil.parser
from django.db.models import Count
import pytz
import datetime
from django.db.models import Max
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from random import shuffle
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
from django.forms.models import modelformset_factory
from tigacrafting.forms import AnnotationForm, MovelabAnnotationForm, ExpertReportAnnotationForm, SuperExpertReportAnnotationForm, PhotoGrid
from tigaserver_app.models import Notification
from zipfile import ZipFile
from io import BytesIO
from operator import attrgetter
from django.db.models import Q
from django.contrib.auth.models import User, Group
import urllib
import django.utils.html
from itertools import chain

adults_2014_nonstandard_validation = ['72ada355-db35-4636-a462-64e492574a53',
'cbcfde79-9169-4df6-a932-0b81a3dda611',
'f3c49049-1e93-4d4c-86fd-b3e59f433497',
'fedcb450-2b12-4c67-a9d5-37f41e2a7541',
'1FD996B3-1DD0-466E-BF31-F79E5232CE35',
'3B63A97E-FCF3-4055-BB5C-C23722BAB024',
'6f172fd6-88e7-438c-8971-1e4d555f3388',
'4857fbd1-0a36-48cf-a0bb-292ec37f14d1',
'6d68e702-bcab-4167-9a79-b7b82740c204',
'93f38fc0-b6ec-47cf-81f5-ccc6a23d6512',
'2d1a667a-0d81-40c9-92f1-48bf3ffa8c4e',
'7e8a9ad9-e292-4e77-8921-c1a04d735ce0',
'f77e5f7b-74fa-42fb-8f40-cbc06e44aa6f',
'38D944E0-5BDD-46AB-967B-966D25A567CC',
'dec52242-46cf-43a7-9ae6-4992a31242a7',
'cbf721b1-043c-4f8d-a207-989278ba86b9',
'ebc3be25-0a96-4891-8218-0bf8a7ddf398',
'cbb2fb90-880a-47d0-b039-05d07d956259',
'1b13557b-3335-4541-afa9-f120c4ecbe52',
'bbc55265-15c5-46a3-ba73-1f1a552e2f54',
'8cf84708-e74f-40f2-bf3b-b17592744648',
'07a35ff2-3520-44f3-b669-5c8cbdd0db38',
'bee07d9b-4d26-4132-bdca-f67555edf654',
'dbf6b8ad-8ad8-4f84-83aa-d18b3a8f7424',
'dbd4f634-319a-4601-9a2c-74592266d5ea',
'8606EA76-5AAA-45EF-AA31-5D68D590C6BD',
'304d6ceb-a42a-48f6-a701-70800d528e91',
'4dbd7425-a234-4361-bb52-3084f506d395',
'18d02734-0591-4d91-b4e1-a9944911b0f5',
'decd43cd-fd41-483a-913c-20c5aff537c6',
'50ed24b4-0d9f-4e52-a138-c9dc47d35e73',
'D9FA6A43-AAAB-429B-ACD0-56435344A564',
'704a3dc1-736d-41b4-ba36-e829246f2197',
'15accaf1-a103-4d2e-97ab-62fe59a9950e',
'e7f9ea53-e62e-428b-b23f-14b864b1f6c7',
'4D55285E-D512-41A6-9F81-9BF48D26634E',
'0fd3a825-0479-4a5f-b330-e09320569074',
'cd91c297-c267-4027-be1f-58ef8e747dfc',
'351d46b4-bae7-412f-856a-8ff594272f31',
'95FBD75E-E3AD-4013-84AF-0D9BB3482EBA',
'92bd0d74-baf6-4055-a68d-d74ded12b621',
'678B04FA-D05E-4A34-85AD-6206F0084F2A',
'9cfbddd8-6c2b-4f21-96be-4381dcf660bb',
'3df9844b-d237-4582-a651-4a95b3039a7b',
'82D3F2C5-1B37-4DBC-A07C-4C2A356C0C13',
'ca0b2a92-4b8b-4e9c-b2e4-93f30296006f',
'de5305b7-ee0b-47a9-991b-9118f74526e7',
'2890D03D-0533-4974-B2F0-3F26FE0E63FF',
'CAD2F906-5797-4B21-9DB7-BA4A401ADAE4',
'cd421aa7-e312-4c2d-a153-5e6ca9697f9b',
'd5016a73-4fff-4e40-887a-d59a1a6e7137',
'6a85b351-6cce-47f7-adff-8c2a1eee424b',
'ee86f3a6-cdaf-4198-8d6f-a3ecdc88dad1',
'9b469815-0605-4ae7-bc82-41b5eb56c0fc',
'39f5f41e-def0-4429-8c68-fa7cae15aee2',
'aa9878f7-4f9c-4a7c-aeb7-56f05831d1de',
'75d0b85b-6fcc-4c08-96bb-bf9a8ef2b09b',
'0a526c37-7a56-44d3-a832-825c8f6c35f1',
'81953CAA-C761-4FDB-8730-C73444BA6420',
'e432abd9-466c-43fb-914b-3a30172e7234',
'4D65375F-B30A-4CE2-B0CA-87C0479A498B',
'ae603cf7-64f5-4049-80a9-d79716008bab',
'ef9119eb-a64d-4123-b4e6-88b19a86ee48',
'179621c0-7948-44ea-b38f-6c0b835fd955',
'0C34A49C-D78B-4647-974A-10933A32CD9B',
'30aa4207-523d-49de-9c05-b605421d9344',
'126931a0-8e3c-4a16-bdbf-03486123f6fd',
'b7117baf-8fd4-4a3d-a458-030b5275d378',
'969e4369-16d3-40d9-a818-0fb74fbe57a7',
'966872D0-DC4F-4CDE-AF30-C6D190350A5C',
'9e2fa727-3825-465d-b0fb-70bb1db99b7e',
'AC5BFD31-8433-4CB2-BFF5-D5B7A69880E3',
'16558b23-9c48-4c04-8760-7f7a08dddd56',
'9979d3b4-7208-40aa-ae42-bc6fb500ca91',
'B1A20436-55D9-4AB4-BC1A-127E399A4B44',
'657A0443-8EA9-4121-8857-CDE72B7D6F70',
'0595962a-c0cb-4c5a-97c0-f9d896ff39c0',
'43A99EB5-9D06-4F61-AE16-6893EEB6D4B5',
'6e5062b1-ca60-4b6d-8b69-ba6edf683c64',
'75c25285-9d1d-497f-ac90-02b26ee8becc',
'1A2D2568-A013-420A-ADBA-AD72299B3618',
'054392ae-dd0b-498a-9f48-158a402e4c79',
'0F9907D1-8C8F-4A7B-B1AB-8606F7259662',
'c2793ce0-9d84-414b-9f6b-1cdfe4eb9717',
'BF3296B7-1427-4AEA-A627-F82D5DD84E70',
'd8e00522-7d80-4edd-aea3-a64d3e16dcd8',
'10849689-99C8-4D6E-9DBA-4B7AEF977C66',
'e6ddf08e-a432-4a9f-922f-537ad5e51737',
'4FB02031-9D09-4146-9750-94E636EA26DD',
'adbf0d60-a5a1-46f3-a0ea-6a03a02443bf',
'e55fbc6e-9144-497a-8f18-746e1238e027',
'd51e5f99-fce1-4d78-acee-b56ffb821965',
'430593ce-31a2-43c7-b31b-3a3b40f3ca57',
'ca9a9845-3534-4eb1-84cf-e2de050c00c3',
'5e3af45c-08d0-4195-8516-f6dd1c7a570f',
'cf22f6e3-f7ff-4500-8179-21dc454d8253',
'ab92ba64-f6c7-46e3-8ed3-d7c01ac3da8b',
'ec7ab6d6-ddb1-4f9b-9a05-fb3eee97ddd9',
'43e3f368-aae3-4edd-9274-a45aa60331b5',
'30cf0bbb-54d0-4c1b-8cae-0ccaf05f7d8a',
'eda31d30-f8c1-4c60-8a70-454f460d676a',
'182ece30-00f3-4fa8-9efb-80146f040264',
'994c015e-1609-4688-bb0e-30e6d424699c',
'25ef9048-9623-4425-92d8-8e45962ecf31',
'a88ff212-21cd-4d5e-91b3-e39b3dd33e14',
'38d184c6-f3f8-492b-aa6d-0cf75c5599a8',
'5e9b352d-fe5f-4e2d-be7a-cbe0db8469ae',
'0006ef72-caa3-479a-9ac8-7ac27fc8de22',
'78045202-a6f1-4ff2-87b4-139ef697723e',
'c4358148-6076-45a1-bdc2-2b72e1342a65',
'a174e5cd-7592-4a5f-bce7-f133b9c4e8ad',
'07b3dc38-99ba-494b-afe4-538e5245afde',
'905EA008-1954-4F3B-9F4F-475C64EB041F',
'528c69a0-7cf5-4eb4-ada3-ac5072fb8e6e',
'19fe3cf8-6b21-44ea-9772-bb347fb43f33',
'5B3E21DF-799B-48F4-85A4-3030028068BB',
'22a2e3b6-f72f-4436-9269-bea77d286b1c',
'99248ee5-7739-4d74-92b1-bebbe1782242',
'dd562a07-8634-4782-bf88-308df0df9124',
'0ae6f50a-bf53-4f37-ad0d-667a75e5aa43',
'c1e01033-719c-4e29-b86d-19ee479fd0f2',
'ee9bdfc0-29bc-4eda-acb9-cc9b7746a8a4',
'FC51513D-E96C-46AE-9D92-F24328908AF9',
'9a637788-35a8-42ee-833b-95e5abfc7f1e',
'399bfa29-c5c5-411f-b31c-0c55adc95055',
'66ca6b0f-0fc9-458e-bc5e-1dd57f216470',
'474e1c44-ab14-449f-bae8-7ed771fbc3e9',
'5ade0d2d-25ee-4589-8edc-8db059b5e335',
'4eae364a-58a6-4ace-b7a2-b0c84b0ef531',
'85f0c4b4-27e6-4234-a958-27103af20101',
'344f04a9-26fa-49b7-9d70-82f6ead2350e',
'25286a53-9928-4093-91f4-93110473dc92',
'1ce96ae4-751f-4564-976c-bb3b0b1f8802',
'ca99bbdd-550c-40a1-890b-13ea0b3499af',
'23c49ef7-9316-4fc0-83cb-61cbfbc2864a',
'fa28260a-ca8e-41cb-9ddd-1ffa704f0708',
'BA6C461A-86E5-4BF8-9528-4603B9B06253',
'E94B2541-90E7-4936-A1B7-339D7B19A645',
'A8307B3D-5AAE-4E3C-AF2E-18C64658CA68',
'c0063f9c-f1ef-4877-a6ae-6ea7834de3e8',
'dbf99045-b99e-47b5-9fd1-57e6d456f9a6',
'4077162f-2e14-4035-b496-7f8049bb3d82',
'895d387b-5848-496e-b866-67fded7e2fc4',
'4b711ea5-5e29-4415-bbf3-1c8844658665',
'6717ff02-7ca5-4ef2-874b-cc98b29de81e',
'a1fee57b-24c2-4fd4-afae-96b2b5c96e4c',
'8314682E-986A-499D-B771-B62DFD1EB9C2',
'473a32f5-f037-45d8-a9d9-b4f5f86c54d3',
'E18452DA-BF5C-485D-8738-F067DDBD01BB',
'11d315ac-855e-4e58-afc6-a8cd6c85a39e',
'62cc9f4c-964a-4a8b-b2f5-e58142673d3e',
'be08a2b8-1de4-4200-8c91-071a2d8dfdec',
'F672CC05-5A85-4A85-AF20-7EE33370D133',
'B3C33276-9935-4B86-B0CB-46049B4EBABA',
'95059889-f903-407a-84a6-ad9f4f8fe999',
'e4c5446e-66b2-44a1-8f6f-07dbefc03fd3',
'7ffb4c05-5ec7-4dec-8c6a-da0ca409d234',
'd842f5eb-1c64-4320-bc35-ccb965d73df1',
'4D8B2966-947E-4F08-B5F4-9120DEF90C23',
'fc7d9135-3168-4215-b0ea-eb96e563b1c2',
'3dc2f4a6-5323-4be0-9b78-32f0cda703c0',
'00b00389-af97-4d64-a04f-bf4871d6e2d9',
'91eaff7f-db71-4a91-98a7-95e37862a53b',
'7c238b62-09fc-445d-b1bb-008061b5014b',
'1c3aa826-33e0-4779-98ed-186bbb622f63',
'e88d90b4-b0d5-423c-9425-f4177acc1fdc',
'1d3af600-7223-498e-a2c6-7da98fba8430',
'fba04fb4-593e-4f08-ad3c-4e66f89f9f07',
'b8e5c84e-7270-4e56-9b6d-f26565e4c526',
'60BF0E01-32E7-4F98-99AD-41C215D64A09',
'ca6638ba-1d69-498f-abd6-b5287ff413ef',
'8a90b6b9-fd65-467a-be85-7a0436bc8c2b',
'dc6fc4ec-943d-46a9-be14-ae1b05420344',
'13cd8abe-4672-4a68-ad43-13a5f4542d7c',
'7a401d75-7cf5-4f5e-8659-701f7c1a71f2',
'bac63568-9047-47e9-b4fb-4d3381a2030f',
'BA5C57DA-B018-4998-A062-27662BF5CB58',
'6217C271-11F8-49BD-81F4-D93F046E547A',
'AFBBAE01-67E4-41C3-A036-C2871E0E09E8',
'4b314f4e-6b2e-46e5-8049-1648d83cb618',
'e54042a0-55d8-484a-bc14-a1f18151790c',
'302e09e9-54ed-4ad1-a2db-fecd1d48201c',
'7503A0C8-8CB8-4310-93E1-D3176CA7DEF4',
'B6C5D906-0F76-4B75-B75D-386D4329E773',
'7D8EC9AB-E7B1-4382-90CF-696C6C4486C1',
'b056f913-3fab-4127-b5d8-6e34c21e5e76',
'1586591E-71B7-491E-AD45-C362F52B8A23',
'5ae25f7d-8b8a-451b-8a02-acf32c13aede',
'5df947d4-bbfa-46ba-8be6-d4555eb84568',
'd4b393ee-e2ed-43ad-9044-41fd2db18a65',
'ED6E686F-75D6-4BE0-906B-774018E5D796',
'b06ba2b2-a18d-4bb4-a551-1df56b3e96d3',
'814de6b1-8abb-40a9-b6c2-b7e0852b9867',
'e63e66e1-ad70-491c-91d5-59a650465202',
'48E07D54-A9C5-4A12-B59E-3563B582C9B7',
'd4accd68-21a6-4862-adfc-5b052dab976d',
'574aed0f-6afd-4465-9215-26ad0a830b3c',
'14ac89b4-bf8b-4d06-a3ed-33c5e5ed1ce0',
'43BC472B-2BCA-46C3-92C4-185DA032C63C',
'cefd49f0-9a05-4c51-9f10-89b36b085a48',
'42dc76e2-487a-4da9-951a-ff2ac55fac23',
'58C3747C-8443-4D5F-BB50-8BEAD59D9001',
'42C0CB3E-99D8-4644-B124-2953223C3E72',
'373f6d30-a3d3-4e81-9759-487d9a9916ec',
'13b01939-f144-4a2b-a5a9-b28c4c50da79',
'CC36FC58-D25D-468B-B317-A39F9D581E75',
'd484fd81-823f-41b6-9dec-28152e5f6b63',
'b185dc8c-d5d6-4643-95b8-aae9d6bcbd93',
'b5392b98-8827-47be-b843-7f30e4c52575',
'c2986dcd-7565-4c9e-bf0b-f722a203d9e1',
'8898c901-c2e6-42cf-8d93-8b43a0081076',
'cb6c12af-3450-4bbb-9359-924d2a5d0a87',
'703D20FC-DBC7-44EF-9CF8-31F2FD74737D',
'76b3c8f1-548e-4db1-bfb7-7ccd196d8c2e',
'1b7094e5-a8b7-4336-a274-0ede3acc6030',
'd28f140b-9835-4e53-bddd-3cc27d1c4549',
'42e2521d-9e08-4ad6-82da-7d8e0b68e960',
'0EF0C957-E961-4433-9919-78A2DB37E8FB',
'dcf413cd-9ad5-46a2-892b-3d282e4e9834',
'8c6bf2df-b8ad-41b5-9d36-fb5ca0653eca',
'4829f046-af36-4a09-a410-2611daa7deef',
'a574a299-d418-4317-8e4c-7d8fefe3b2c9',
'cbfaeb71-2c0e-4ee8-8b9a-efd98fbe5ae0',
'e2f12cea-cf87-441d-b04c-32d39b8d4a07',
'D8598C3D-C6E8-4A9C-8A56-3E30D2E18BE8',
'01671cc6-1c47-4cc6-8839-447327dfb7ab',
'da9307c9-7601-4e18-9c80-c11b99c6ed10',
'0fdcd15d-6dea-4b17-8c75-6848c3e30ad8',
'de2d49eb-7248-483a-a8c4-267737c3e80b',
'b67cc071-385b-4a20-bc57-91ad21d74b25',
'fe5d36f1-b3d0-4662-b551-cbace2bd0d9a',
'111f108c-2057-46eb-b124-29dfc457c0aa',
'edb54c2c-6941-4c10-8d40-1047ac21bff8',
'8B406F7A-160F-4244-8756-07CD11A2662A',
'b03b5fca-c2c6-4cdc-b22b-1666bb98cf58',
'9C35C8AF-4A75-4844-A9EF-3D362BC98435',
'2a55263e-e51e-49f3-af14-412bc3e39f49',
'85cfd62c-3869-4dee-a8ee-cf954ecb673e',
'E17A12E6-ECB1-45BB-B655-EDD52BEEC7B7',
'3824d99c-9d59-4a64-b2bb-814e58566626',
'631acfa5-b6b6-4cfb-9ee2-26f9d7fdf35a',
'7e8734e6-9aaa-438d-94cf-844e48d6f564',
'6b429b01-daa3-430d-8075-0e1cf9bad4fd',
'2ba70455-9047-4b00-a196-0440d308d5d9',
'78A9648E-BC6C-47F3-9F0F-60D9BB0060DB',
'd2912add-e84d-4cb4-8e3b-7ed558ab155a',
'1126ac48-e4c6-4480-ae7a-66e6485fd3b3',
'e8d5cebc-c6b8-4a7d-9aa3-7c34a0f28f6a',
'862dc9a3-516c-40ec-bb59-8160d5ef857c',
'65807d48-dc0b-41e8-8eb5-3c0a2aa373a7',
'916BCEA0-227C-4BCD-A6D3-9BF4D4C2A98E',
'B7E25F46-FE39-403F-A9E3-6AF2D107FF70',
'b78e7424-2b81-4966-818c-a6cf08b69bc4',
'abd91b5e-8637-45d7-8d58-355bf71004b5',
'17BE589A-A919-4868-A978-6C836338A984',
'b0b298d8-d065-4f1e-b878-37c36d716ab6',
'2189C7B6-CE1C-48DD-9252-C82734CBFDBA',
'F8087CDF-0E84-47AC-9E23-67CB5F8FE840',
'c73cc372-31fb-4f9f-b885-ddda33122f19',
'1d0373bc-0a03-4fe3-89b0-8693522b1c99',
'24AA5110-8AB8-42AE-816E-D8B3E9E16A4D',
'0F3A5BAC-2370-41C0-A4E6-75EA061B6352',
'af4a4279-43d0-40da-ad56-3e43a009027b',
'0573d2b3-bd4b-4275-ba43-364780303d8d',
'6e42a69c-d8e9-44ca-aed6-29f895da9e36',
'6dfb248b-a50a-4dd3-a2e7-7edb4d802339',
'681F6A1E-5CEA-483F-BFB8-05D56236BEC2',
'203cad94-656d-43f3-9fec-1151f76b68f4',
'e22ca6aa-1717-499e-a771-0be9ac005a31',
'75211565-0e23-4207-91f5-b41894b9d2d9',
'f9bbf7c1-a36d-4b42-9bee-b09b77d7fa9e',
'bc515908-16fe-443c-be23-0e8d5ac00307',
'c66f1fc8-dbba-4ef5-81a2-9f022cf02eda',
'8008C9C4-E422-430D-BFBD-E83F64F5EB84',
'2e9c02dc-6df6-490f-9001-d30101244055',
'9ac5478e-977f-4a88-a8c6-3114bbd34fd5',
'6fa510bc-92b3-493c-8cb3-a271e1600745',
'8255A895-D560-4E5A-8DE3-D1E163292839',
'0d205c10-354b-489e-96ab-97d075cb32f5',
'4ce39ba2-34cc-4743-964f-2ae5aaf50f0f',
'6BEB695D-8DBA-4D11-BF7B-24EFED5262A1',
'ceeef501-ab91-425d-b8de-b2d23c168ec5',
'7E260B1E-CAA1-4F9F-A0CF-6B57F36B24A7',
'7b2fe3be-a5db-4406-807e-b10371f69cee',
'674d9840-9d60-4a9c-90aa-dc6935e5195f',
'935518bd-e136-4575-9b39-306e4a4f4cec',
'82a22fc3-174f-4d85-b65c-9b4b09a93c83',
'1EB99C7F-5A27-4BC7-BAD9-8C84F3FF396E',
'cc89e741-03a8-4269-b425-51d57f203a3d',
'6062479D-1259-44FE-ADC3-64F1C6239CC1',
'aced34a6-b5c9-45e1-acba-71ee4a0ff29e',
'fa3f7e04-615c-4a7f-9e6e-a831e731d347',
'59df912e-f450-47dc-8984-9fd0ebebbefd',
'326EC7D6-6517-4D62-87C0-89BEED0BA008']

def get_current_domain(request):
    if request.META['HTTP_HOST'] != '':
        return request.META['HTTP_HOST']
    if settings.DEBUG:
        current_domain = 'humboldt.ceab.csic.es'
    else:
        current_domain = 'tigaserver.atrapaeltigre.com'
    return current_domain


def photos_to_tasks():
    these_photos = Photo.objects.filter(crowdcraftingtask=None).exclude(report__hide=True).exclude(hide=True)
    if these_photos:
        for p in these_photos:
            new_task = CrowdcraftingTask()
            new_task.photo = p
            new_task.save()


def import_tasks():
    errors = []
    warnings = []
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task&format=json')
    try:
        task_array = json.loads(r.text)
    except ValueError:
        zipped_file = ZipFile(BytesIO(r.content))
        task_array = json.loads(zipped_file.open(zipped_file.namelist()[0]).read())
    last_task_id = CrowdcraftingTask.objects.all().aggregate(Max('task_id'))['task_id__max']
    if last_task_id:
        new_tasks = filter(lambda x: x['id'] > last_task_id, task_array)
    else:
        new_tasks = task_array
    for task in new_tasks:
        existing_task = CrowdcraftingTask.objects.filter(task_id=task['id'])
        if not existing_task:
            existing_empty_task = CrowdcraftingTask.objects.filter(photo=task['info'][u'\ufeffid'])
            if not existing_empty_task:
                task_model = CrowdcraftingTask()
                task_model.task_id = task['id']
                existing_photo = Photo.objects.filter(id=int(task['info'][u'\ufeffid']))
                if existing_photo:
                    this_photo = Photo.objects.get(id=task['info'][u'\ufeffid'])
                    # check for tasks that already have this photo: There should not be any BUT I accidentially added photos 802-810 in both the first and second crowdcrafting task batches
                    if CrowdcraftingTask.objects.filter(photo=this_photo).count() > 0:
                        # do nothing if photo id beteen 802 and 810 since I already know about this
                        if this_photo.id in range(802, 811):
                            pass
                        else:
                            errors.append('Task with Photo ' + str(this_photo.id) + ' already exists. Not importing this task.')
                    else:
                        task_model.photo = this_photo
                        task_model.save()
                else:
                    errors.append('Photo with id=' + task['info'][u'\ufeffid'] + ' does not exist.')
            else:
                existing_empty_task.task_id = task['id']
                existing_photo = Photo.objects.filter(id=int(task['info'][u'\ufeffid']))
                if existing_photo:
                    this_photo = Photo.objects.get(id=task['info'][u'\ufeffid'])
                    # check for tasks that already have this photo: There should not be any BUT I accidentially added photos 802-810 in both the first and second crowdcrafting task batches
                    if CrowdcraftingTask.objects.filter(photo=this_photo).count() > 0:
                        # do nothing if photo id beteen 802 and 810 since I already know about this
                        if this_photo.id in range(802, 811):
                            pass
                        else:
                            errors.append('Task with Photo ' + str(this_photo.id) + ' already exists. Not importing this task.')
                    else:
                        existing_empty_task.photo = this_photo
                        existing_empty_task.save()
                else:
                    errors.append('Photo with id=' + task['info'][u'\ufeffid'] + ' does not exist.')
        else:
            warnings.append('Task ' + str(existing_task[0].task_id) + ' already exists, not saved.')
    # write errors and warnings to files that we can check
    if len(errors) > 0 or len(warnings) > 0:
        barcelona = pytz.timezone('Europe/Paris')
        ef = open(settings.MEDIA_ROOT + 'crowdcrafting_error_log.html', 'a')
        if len(errors) > 0:
            ef.write('<h1>tigacrafting.views.import_tasks errors</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(errors) + '</p>')
        if len(warnings) > 0:
            ef.write('<h1>tigacrafting.views.import_tasks warnings</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(warnings) + '</p>')
        ef.close()
        print '\n'.join(errors)
        print '\n'.join(warnings)
    return {'errors': errors, 'warnings': warnings}


def import_task_responses():
    errors = []
    warnings = []
    r = requests.get('http://crowdcrafting.org/app/Tigafotos/tasks/export?type=task_run&format=json')
    try:
        response_array = json.loads(r.text)
    except ValueError:
        zipped_file = ZipFile(BytesIO(r.content))
        response_array = json.loads(zipped_file.open(zipped_file.namelist()[0]).read())
    last_response_id = CrowdcraftingResponse.objects.all().aggregate(Max('response_id'))['response_id__max']
    if last_response_id:
        new_responses = filter(lambda x: x['id'] > last_response_id, response_array)
    else:
       new_responses = response_array
    for response in new_responses:
        existing_response = CrowdcraftingResponse.objects.filter(response_id=int(response['id']))
        if existing_response:
            warnings.append('Response to task ' + str(response['task_id']) + ' by user ' + str(response['user_id']) + ' already exists. Skipping this response.')
        else:
            info_dic = {}
            info_fields = response['info'].replace('{', '').replace(' ', '').replace('}', '').split(',')
            for info_field in info_fields:
                info_dic[info_field.split(':')[0]] = info_field.split(':')[1]
            response_model = CrowdcraftingResponse()
            response_model.response_id = int(response['id'])
            creation_time = dateutil.parser.parse(response['created'])
            creation_time_localized = pytz.utc.localize(creation_time)
            response_model.created = creation_time_localized
            finish_time = dateutil.parser.parse(response['finish_time'])
            finish_time_localized = pytz.utc.localize(finish_time)
            response_model.finish_time = finish_time_localized
            response_model.mosquito_question_response = info_dic['mosquito']
            response_model.tiger_question_response = info_dic['tiger']
            response_model.site_question_response = info_dic['site']
            response_model.user_ip = response['user_ip']
            response_model.user_lang = info_dic['user_lang']
            existing_task = CrowdcraftingTask.objects.filter(task_id=response['task_id'])
            if existing_task:
                print 'existing task'
                this_task = CrowdcraftingTask.objects.get(task_id=response['task_id'])
                response_model.task = this_task
            else:
                import_tasks()
                warnings.append('Task ' + str(response['task_id']) + ' did not exist, so import_tasks was called.')
                existing_task = CrowdcraftingTask.objects.filter(task_id=response['task_id'])
                if existing_task:
                    this_task = CrowdcraftingTask.objects.get(task_id=response['task_id'])
                    response_model.task = this_task
                else:
                    errors.append('Cannot seem to import task ' + str(response['task_id']))
                    continue
            existing_user = CrowdcraftingUser.objects.filter(user_id=response['user_id'])
            if existing_user:
                this_user = CrowdcraftingUser.objects.get(user_id=response['user_id'])
                response_model.user = this_user
            else:
                this_user = CrowdcraftingUser()
                this_user.user_id = response['user_id']
                this_user.save()
                response_model.user = this_user
            response_model.save()
    # write errors and warnings to files that we can check
    barcelona = pytz.timezone('Europe/Paris')
    if len(errors) > 0 or len(warnings) > 0:
        ef = open(settings.MEDIA_ROOT + 'crowdcrafting_error_log.html', 'a')
        if len(errors) > 0:
            ef.write('<h1>tigacrafting.views.import_task_responses errors</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(errors) + '</p>')
        if len(warnings) > 0:
            ef.write('<h1>tigacrafting.views.import_task_responses warnings</h1><p>' + barcelona.localize(datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S UTC%z') + '</p><p>' + '</p><p>'.join(warnings) + '</p>')
        ef.close()
      #  print '\n'.join(errors)
      #  print '\n'.join(warnings)
    return {'errors': errors, 'warnings': warnings}


def show_processing(request):
    return render(request, 'tigacrafting/please_wait.html')


def filter_tasks(tasks):
    tasks_filtered = filter(lambda x: not x.photo.report.deleted and x.photo.report.latest_version, tasks)
    return tasks_filtered


def filter_reports(reports, sort=True):
    if sort:
        reports_filtered = sorted(filter(lambda x: not x.deleted and x.latest_version, reports), key=attrgetter('n_annotations'), reverse=True)
    else:
        reports_filtered = filter(lambda x: not x.deleted and x.latest_version, reports)
    return reports_filtered


def filter_reports_for_superexpert(reports):
    reports_filtered = filter(lambda x: not x.deleted and x.latest_version and len(filter(lambda y: y.is_expert() and y.validation_complete, x.expert_report_annotations.all()))>=3, reports)
    return reports_filtered


@xframe_options_exempt
def show_validated_photos(request, type='tiger'):
    title_dic = {'mosquito': 'Mosquito Validation Results', 'site': 'Breeding Site Validation Results', 'tiger': 'Tiger Mosquito Validation Results'}
    question_dic = {'mosquito': 'Do you see a mosquito in this photo?', 'site': 'Do you see a potential tiger mosquito breeding site in this photo?', 'tiger': 'Is this a tiger mosquito?'}
    validation_score_dic = {'mosquito': 'mosquito_validation_score', 'site': 'site_validation_score', 'tiger': 'tiger_validation_score'}
    individual_responses_dic = {'mosquito': 'mosquito_individual_responses_html', 'site': 'site_individual_responses_html', 'tiger': 'tiger_individual_responses_html'}
    import_task_responses()
    validated_tasks = CrowdcraftingTask.objects.annotate(n_responses=Count('responses')).filter(n_responses__gte=30).exclude(photo__report__hide=True).exclude(photo__hide=True)
    validated_tasks_filtered = filter_tasks(validated_tasks)
    validated_task_array = sorted(map(lambda x: {'id': x.id, 'report_type': x.photo.report.type, 'report_creation_time': x.photo.report.creation_time.strftime('%d %b %Y, %H:%M %Z'), 'lat': x.photo.report.lat, 'lon':  x.photo.report.lon, 'photo_image': x.photo.medium_image_(), 'validation_score': round(getattr(x, validation_score_dic[type]), 2), 'neg_validation_score': -1*round(getattr(x, validation_score_dic[type]), 2), 'individual_responses_html': getattr(x, individual_responses_dic[type])}, list(validated_tasks_filtered)), key=lambda x: -x['validation_score'])
    paginator = Paginator(validated_task_array, 25)
    page = request.GET.get('page')
    try:
        these_validated_tasks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        these_validated_tasks = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        these_validated_tasks = paginator.page(paginator.num_pages)
    context = {'type': type, 'title': title_dic[type], 'n_tasks': len(validated_task_array), 'question': question_dic[type], 'validated_tasks': these_validated_tasks}
    return render(request, 'tigacrafting/validated_photos.html', context)


@login_required
def annotate_tasks(request, how_many=None, which='new', scroll_position=''):
    this_user = request.user
    args = {}
    args.update(csrf(request))
    args['scroll_position'] = scroll_position
    AnnotationFormset = modelformset_factory(Annotation, form=AnnotationForm, extra=0)
    if request.method == 'POST':
        scroll_position = request.POST.get("scroll_position", '0')
        formset = AnnotationFormset(request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('annotate_tasks_scroll_position', kwargs={'which': 'working_on', 'scroll_position': scroll_position}))
        else:
            return HttpResponse('error')
    else:
        if which == 'noted_only':
            Annotation.objects.filter(working_on=True).update(working_on=False)
            this_queryset = Annotation.objects.filter(user=request.user, value_changed=False).exclude(notes="")
            this_queryset.update(working_on=True)
            this_formset = AnnotationFormset(queryset=this_queryset)
        if which == 'completed':
            Annotation.objects.filter(working_on=True).update(working_on=False)
            this_queryset = Annotation.objects.filter(user=request.user).exclude( tiger_certainty_percent=None).exclude(value_changed=False)
            this_queryset.update(working_on=True)
            this_formset = AnnotationFormset(queryset=this_queryset)
        if which == 'working_on':
            this_formset = AnnotationFormset(queryset=Annotation.objects.filter(user=request.user, working_on=True))
        if which == 'new':
            import_task_responses()
            annotated_task_ids = Annotation.objects.filter(user=this_user).exclude(tiger_certainty_percent=None).exclude(value_changed=False).values('task__id')
            validated_tasks = CrowdcraftingTask.objects.exclude(id__in=annotated_task_ids).exclude(photo__report__hide=True).exclude(photo__hide=True).filter(photo__report__type='adult').annotate(n_responses=Count('responses')).filter(n_responses__gte=30)
            validated_tasks_filtered = filter_tasks(validated_tasks)
            shuffle(validated_tasks_filtered)
            if how_many is not None:
                task_sample = validated_tasks_filtered[:int(how_many)]
            else:
                task_sample = validated_tasks_filtered
            # reset working_on annotations
            Annotation.objects.filter(working_on=True).update(working_on=False)
            # set working on for existing annotations:
            Annotation.objects.filter(user=this_user, task__in=task_sample).update(working_on=True)
            # make blank annotations for this user as needed
            for this_task in task_sample:
                if not Annotation.objects.filter(user=this_user, task=this_task).exists():
                    new_annotation = Annotation(user=this_user, task=this_task, working_on=True)
                    new_annotation.save()
            this_formset = AnnotationFormset(queryset=Annotation.objects.filter(user=request.user, task__in=task_sample))
        args['formset'] = this_formset
        return render(request, 'tigacrafting/expert_validation.html', args)


@login_required
def movelab_annotation(request, scroll_position='', tasks_per_page='50', type='all'):
    this_user = request.user
    if request.user.groups.filter(name='movelab').exists():
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        AnnotationFormset = modelformset_factory(MoveLabAnnotation, form=MovelabAnnotationForm, extra=0)
        if request.method == 'POST':
            scroll_position = request.POST.get("scroll_position", '0')
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                formset.save()
                page = request.GET.get('page')
                if not page:
                    page = '1'
                if type == 'pending':
                    return HttpResponseRedirect(reverse('movelab_annotation_pending_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
                else:
                    return HttpResponseRedirect(reverse('movelab_annotation_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
            else:
                return HttpResponse('error')
        else:
            photos_to_tasks()
            import_tasks()
            tasks_without_annotations_unfiltered = CrowdcraftingTask.objects.exclude(photo__report__hide=True).exclude(photo__hide=True).filter(movelab_annotation=None)
            tasks_without_annotations = filter_tasks(tasks_without_annotations_unfiltered)
            for this_task in tasks_without_annotations:
                new_annotation = MoveLabAnnotation(task=this_task)
                new_annotation.save()
            all_annotations = MoveLabAnnotation.objects.all().order_by('id')
            if type == 'pending':
                all_annotations = all_annotations.exclude(tiger_certainty_category__in=[-2, -1, 0, 1, 2])
            paginator = Paginator(all_annotations, int(tasks_per_page))
            page = request.GET.get('page')
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                objects = paginator.page(1)
            except EmptyPage:
                objects = paginator.page(paginator.num_pages)
            page_query = all_annotations.filter(id__in=[object.id for object in objects])
            this_formset = AnnotationFormset(queryset=page_query)
            args['formset'] = this_formset
            args['objects'] = objects
            args['pages'] = range(1, objects.paginator.num_pages+1)
            args['tasks_per_page_choices'] = range(25, min(200, all_annotations.count())+1, 25)
        return render(request, 'tigacrafting/movelab_validation.html', args)
    else:
        return HttpResponse("You need to be logged in as a MoveLab member to view this page.")


@login_required
def movelab_annotation_pending(request, scroll_position='', tasks_per_page='50', type='pending'):
    this_user = request.user
    if request.user.groups.filter(name='movelab').exists():
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        AnnotationFormset = modelformset_factory(MoveLabAnnotation, form=MovelabAnnotationForm, extra=0)
        if request.method == 'POST':
            scroll_position = request.POST.get("scroll_position", '0')
            formset = AnnotationFormset(request.POST)
            if formset.is_valid():
                formset.save()
                page = request.GET.get('page')
                if not page:
                    page = '1'
                if type == 'pending':
                    return HttpResponseRedirect(reverse('movelab_annotation_pending_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
                else:
                    return HttpResponseRedirect(reverse('movelab_annotation_scroll_position', kwargs={'tasks_per_page': tasks_per_page, 'scroll_position': scroll_position}) + '?page='+page)
            else:
                return HttpResponse('error')
        else:
            photos_to_tasks()
            import_tasks()
            tasks_without_annotations_unfiltered = CrowdcraftingTask.objects.exclude(photo__report__hide=True).exclude(photo__hide=True).filter(movelab_annotation=None)
            tasks_without_annotations = filter_tasks(tasks_without_annotations_unfiltered)
            for this_task in tasks_without_annotations:
                new_annotation = MoveLabAnnotation(task=this_task)
                new_annotation.save()
            all_annotations = MoveLabAnnotation.objects.all().order_by('id')
            if type == 'pending':
                all_annotations = all_annotations.exclude(tiger_certainty_category__in=[-2, -1, 0, 1, 2])
            paginator = Paginator(all_annotations, int(tasks_per_page))
            page = request.GET.get('page')
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                objects = paginator.page(1)
            except EmptyPage:
                objects = paginator.page(paginator.num_pages)
            page_query = all_annotations.filter(id__in=[object.id for object in objects])
            this_formset = AnnotationFormset(queryset=page_query)
            args['formset'] = this_formset
            args['objects'] = objects
            args['pages'] = range(1, objects.paginator.num_pages+1)
            args['tasks_per_page_choices'] = range(25, min(200, all_annotations.count())+1, 25)
        return render(request, 'tigacrafting/movelab_validation.html', args)
    else:
        return HttpResponse("You need to be logged in as a MoveLab member to view this page.")


BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}

def autoflag_others(id_annotation_report):
    this_annotation = ExpertReportAnnotation.objects.get(id=id_annotation_report)
    the_report = this_annotation.report
    annotations = ExpertReportAnnotation.objects.filter(report_id=the_report.version_UUID).filter(user__groups__name='expert')
    for anno in annotations:
        if anno.id != id_annotation_report:
            anno.status = 0
            anno.save()


def must_be_autoflagged(this_annotation, is_current_validated):
    if this_annotation is not None:
        the_report = this_annotation.report
        if the_report is not None:
            annotations = ExpertReportAnnotation.objects.filter(report_id=the_report.version_UUID, user__groups__name='expert').exclude(id=this_annotation.id)
            anno_count = 0
            one_positive_albopictus = False
            one_positive_aegypti = False
            one_unclassified_or_inconclusive = False
            for anno in annotations:
                validated = anno.validation_complete
                if anno.tiger_certainty_category is not None and anno.tiger_certainty_category > 0 and validated == True:
                    one_positive_albopictus = True
                if anno.aegypti_certainty_category is not None and anno.aegypti_certainty_category > 0 and validated == True:
                    one_positive_aegypti = True
                if anno.aegypti_certainty_category is not None and anno.aegypti_certainty_category <= 0 \
                        and anno.tiger_certainty_category is not None and anno.tiger_certainty_category <= 0 \
                        and validated == True:
                    one_unclassified_or_inconclusive = True
                if anno.aegypti_certainty_category is None and anno.tiger_certainty_category is None and validated == True:
                    one_unclassified_or_inconclusive = True
                anno_count += 1
            validated = is_current_validated
            if this_annotation.tiger_certainty_category is not None and this_annotation.tiger_certainty_category > 0 and validated == True:
                one_positive_albopictus = True
            if this_annotation.aegypti_certainty_category is not None and this_annotation.aegypti_certainty_category > 0 and validated == True:
                one_positive_aegypti = True
            if this_annotation.aegypti_certainty_category is not None and this_annotation.aegypti_certainty_category <= 0 \
                    and this_annotation.tiger_certainty_category is not None and this_annotation.tiger_certainty_category <= 0 \
                    and validated == True:
                one_unclassified_or_inconclusive = True
            if this_annotation.aegypti_certainty_category is None and this_annotation.tiger_certainty_category is None and validated == True:
                one_unclassified_or_inconclusive = True

            if one_positive_albopictus and one_positive_aegypti and one_unclassified_or_inconclusive and (anno_count + 1) == 3:
                return True
    return False

# This can be called from outside the server, so we need current_domain for absolute urls
def issue_notification(report_annotation,current_domain):
    notification = Notification(report=report_annotation.report,user=report_annotation.report.user,expert=report_annotation.user)
    notification.expert_comment = "¡Uno de sus informes ha sido validado por un experto!"
    if report_annotation.report.get_final_photo_url_for_notification():
        notification.expert_html = '<a href="http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification() + '" target="_blank">Enlace a tu foto</a>'
    if report_annotation.message_for_user:
        clean_annotation = ''
        clean_annotation = django.utils.html.escape(report_annotation.message_for_user)
        clean_annotation = clean_annotation.encode('ascii', 'xmlcharrefreplace')
        notification.expert_html = notification.expert_html + "</br> Mensaje de los expertos: </br>" + clean_annotation
    photo = None
    if report_annotation.report.get_final_photo_url_for_notification():
        photo = 'http://' + current_domain + report_annotation.report.get_final_photo_url_for_notification()
    if photo:
        notification.photo_url = photo
    notification.save()

@login_required
def expert_report_annotation(request, scroll_position='', tasks_per_page='10', note_language='es', load_new_reports='F', year='all', orderby='date', tiger_certainty='all', site_certainty='all', pending='na', checked='na', status='all', final_status='na', max_pending=5, max_given=3, version_uuid='na', linked_id='na', edit_mode='off', tags_filter='na'):
    this_user = request.user
    current_domain = get_current_domain(request)
    this_user_is_expert = this_user.groups.filter(name='expert').exists()
    this_user_is_superexpert = this_user.groups.filter(name='superexpert').exists()
    this_user_is_team_bcn = this_user.groups.filter(name='team_bcn').exists()
    this_user_is_team_not_bcn = this_user.groups.filter(name='team_not_bcn').exists()
    this_user_is_reritja = (this_user.id == 25)

    if this_user_is_expert or this_user_is_superexpert:
        args = {}
        args.update(csrf(request))
        args['scroll_position'] = scroll_position
        if this_user_is_superexpert:
            AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=SuperExpertReportAnnotationForm, extra=0)
        else:
            AnnotationFormset = modelformset_factory(ExpertReportAnnotation, form=ExpertReportAnnotationForm, extra=0)
        if request.method == 'POST':
            scroll_position = request.POST.get("scroll_position", '0')
            orderby = request.POST.get('orderby', orderby)
            tiger_certainty = request.POST.get('tiger_certainty', tiger_certainty)
            site_certainty = request.POST.get('site_certainty', site_certainty)
            pending = request.POST.get('pending', pending)
            status = request.POST.get('status', status)
            final_status = request.POST.get('final_status', final_status)
            version_uuid = request.POST.get('version_uuid', version_uuid)
            linked_id = request.POST.get('linked_id', linked_id)
            tags_filter = request.POST.get('tags_filter', tags_filter)
            checked = request.POST.get('checked', checked)
            tasks_per_page = request.POST.get('tasks_per_page', tasks_per_page)
            note_language = request.GET.get('note_language', "es")
            load_new_reports = request.POST.get('load_new_reports', load_new_reports)
            save_formset = request.POST.get('save_formset', "F")
            if save_formset == "T":
                formset = AnnotationFormset(request.POST)
                if formset.is_valid():
                    for f in formset:
                        one_form = f.save(commit=False)
                        auto_flag = must_be_autoflagged(one_form,one_form.validation_complete)
                        if auto_flag:
                            one_form.status = 0
                        if(this_user_is_reritja and one_form.validation_complete == True):
                            issue_notification(one_form,current_domain)
                        one_form.save()
                        f.save_m2m()
                        if auto_flag:
                            autoflag_others(one_form.id)
                else:
                    return render(request, 'tigacrafting/formset_errors.html', {'formset': formset})
            page = request.POST.get('page')
            if not page:
                page = '1'
            return HttpResponseRedirect(reverse('expert_report_annotation') + '?page='+page+'&tasks_per_page='+tasks_per_page+'&note_language=' + note_language + '&scroll_position='+scroll_position+(('&pending='+pending) if pending else '') + (('&checked='+checked) if checked else '') + (('&final_status='+final_status) if final_status else '') + (('&version_uuid='+version_uuid) if version_uuid else '') + (('&linked_id='+linked_id) if linked_id else '') + (('&orderby='+orderby) if orderby else '') + (('&tiger_certainty='+tiger_certainty) if tiger_certainty else '') + (('&site_certainty='+site_certainty) if site_certainty else '') + (('&status='+status) if status else '') + (('&load_new_reports='+load_new_reports) if load_new_reports else '') + (('&tags_filter=' + urllib.quote_plus(tags_filter)) if tags_filter else ''))
        else:
            tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
            note_language = request.GET.get('note_language', note_language)
            scroll_position = request.GET.get('scroll_position', scroll_position)
            orderby = request.GET.get('orderby', orderby)
            tiger_certainty = request.GET.get('tiger_certainty', tiger_certainty)
            site_certainty = request.GET.get('site_certainty', site_certainty)
            pending = request.GET.get('pending', pending)
            status = request.GET.get('status', status)
            final_status = request.GET.get('final_status', final_status)
            version_uuid = request.GET.get('version_uuid', version_uuid)
            linked_id = request.GET.get('linked_id', linked_id)
            tags_filter = request.GET.get('tags_filter', tags_filter)
            checked = request.GET.get('checked', checked)
            load_new_reports = request.GET.get('load_new_reports', load_new_reports)
            edit_mode = request.GET.get('edit_mode', edit_mode)
        #current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
        current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
        #my_reports = ExpertReportAnnotation.objects.filter(user=this_user).values('report')
        my_reports = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult').values('report').distinct()
        hidden_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True, revise=True, status=-1).values_list('report', flat=True))
        flagged_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True, revise=True, status=0).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True))
        public_final_reports_superexpert = set(ExpertReportAnnotation.objects.filter(user__groups__name='superexpert', validation_complete=True, revise=True, status=1).exclude(report__version_UUID__in=hidden_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True))
        hidden_final_reports = set(list(hidden_final_reports_superexpert) + list(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=-1).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=flagged_final_reports_superexpert).values_list('report', flat=True)))
        flagged_final_reports = set(list(flagged_final_reports_superexpert) + list(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=0).exclude(report__version_UUID__in=public_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True)))
        public_final_reports = set(list(public_final_reports_superexpert) + list(ExpertReportAnnotation.objects.filter(user__groups__name='expert', validation_complete=True, status=1).exclude(report__version_UUID__in=flagged_final_reports_superexpert).exclude(report__version_UUID__in=hidden_final_reports_superexpert).values_list('report', flat=True)))
        if this_user_is_expert and load_new_reports == 'T':
            if current_pending < max_pending:
                n_to_get = max_pending - current_pending
                new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)
                #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)
                #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos=None).filter(type__in=['adult', 'site']).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__lt=max_given)

                if new_reports_unfiltered and this_user_is_team_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']), current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
                if new_reports_unfiltered and this_user_is_team_not_bcn:
                    new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))

                if new_reports_unfiltered:
                    new_reports = filter_reports(new_reports_unfiltered.order_by('creation_time'))
                    reports_to_take = new_reports[0:n_to_get]
                    user_stats = None
                    try:
                        user_stats = UserStat.objects.get(user_id=this_user.id)
                    except ObjectDoesNotExist:
                        pass
                    grabbed_reports = -1
                    if user_stats:
                        grabbed_reports = user_stats.grabbed_reports
                    for this_report in reports_to_take:
                        new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                        who_has_count = this_report.get_who_has_count()
                        if who_has_count == 0 or who_has_count == 1:
                            #No one has the report, is simplified
                            new_annotation.simplified_annotation = True
                        grabbed_reports += 1
                        new_annotation.save()
                    if grabbed_reports != -1 and user_stats:
                        user_stats.grabbed_reports = grabbed_reports
                        user_stats.save()
        elif this_user_is_superexpert:
            new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains="#345").exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)
            #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult').annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)
            #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(version_UUID__in=my_reports).exclude(hide=True).exclude(photos__isnull=True).filter(type__in=['adult', 'site']).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations__gte=max_given)

            if new_reports_unfiltered and this_user_is_team_bcn:
                new_reports_unfiltered = new_reports_unfiltered.filter(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))
            if new_reports_unfiltered and this_user_is_team_not_bcn:
                new_reports_unfiltered = new_reports_unfiltered.exclude(Q(location_choice='selected', selected_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),selected_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])) | Q(location_choice='current', current_location_lon__range=(BCN_BB['min_lon'],BCN_BB['max_lon']),current_location_lat__range=(BCN_BB['min_lat'], BCN_BB['max_lat'])))

            if new_reports_unfiltered:
                new_reports = filter_reports_for_superexpert(new_reports_unfiltered)
                for this_report in new_reports:
                    new_annotation = ExpertReportAnnotation(report=this_report, user=this_user)
                    new_annotation.save()
        #all_annotations = ExpertReportAnnotation.objects.filter(user=this_user)
        all_annotations = ExpertReportAnnotation.objects.filter(user=this_user).filter(report__type='adult')
        my_version_uuids = all_annotations.values('report__version_UUID').distinct()
        my_linked_ids = all_annotations.values('linked_id').distinct()
        if this_user_is_expert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not pending or pending == 'na'):
                pending = 'pending'
        if this_user_is_superexpert:
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not final_status or final_status == 'na'):
                final_status = 'public'
            if (version_uuid == 'na' and linked_id == 'na' and tags_filter == 'na') and (not checked or checked == 'na'):
                checked = 'unchecked'
            n_flagged = all_annotations.filter(report__in=flagged_final_reports).count()
            n_hidden = all_annotations.filter(report__in=hidden_final_reports).count()
            n_public = all_annotations.filter(report__in=public_final_reports).exclude(report__in=flagged_final_reports).exclude(report__in=hidden_final_reports).count()
            n_unchecked = all_annotations.filter(validation_complete=False).count()
            n_confirmed = all_annotations.filter(validation_complete=True, revise=False).count()
            n_revised = all_annotations.filter(validation_complete=True, revise=True).count()
            args['n_flagged'] = n_flagged
            args['n_hidden'] = n_hidden
            args['n_public'] = n_public
            args['n_unchecked'] = n_unchecked
            args['n_confirmed'] = n_confirmed
            args['n_revised'] = n_revised
        if version_uuid and version_uuid != 'na':
            all_annotations = all_annotations.filter(report__version_UUID=version_uuid)
        if linked_id and linked_id != 'na':
            all_annotations = all_annotations.filter(linked_id=linked_id)
        if tags_filter and tags_filter != 'na' and tags_filter!='':
            tags_array = tags_filter.split(",")
            # we must go up to Report to filter tags, because you don't want to filter only your own tags but the tag that
            # any expert has put on the report
            # these are all (not only yours, but also) the reports that contain the filtered tag
            everyones_tagged_reports = ExpertReportAnnotation.objects.filter(tags__name__in=tags_array).values('report').distinct
            # we want the annotations of the reports which contain the tag(s)
            all_annotations = all_annotations.filter(report__in=everyones_tagged_reports)
        if (not version_uuid or version_uuid == 'na') and (not linked_id or linked_id == 'na') and (not tags_filter or tags_filter == 'na' or tags_filter==''):
            if year and year != 'all':
                try:
                    this_year = int(year)
                    all_annotations = all_annotations.filter(report__creation_time__year=this_year)
                except ValueError:
                    pass
            if tiger_certainty and tiger_certainty != 'all':
                try:
                    this_certainty = int(tiger_certainty)
                    all_annotations = all_annotations.filter(tiger_certainty_category=this_certainty)
                except ValueError:
                    pass
            if site_certainty and site_certainty != 'all':
                try:
                    this_certainty = int(site_certainty)
                    all_annotations = all_annotations.filter(site_certainty_category=this_certainty)
                except ValueError:
                    pass

            if pending == "complete":
                all_annotations = all_annotations.filter(validation_complete=True)
            elif pending == 'pending':
                all_annotations = all_annotations.filter(validation_complete=False)
            if status == "flagged":
                all_annotations = all_annotations.filter(status=0)
            elif status == "hidden":
                all_annotations = all_annotations.filter(status=-1)
            elif status == "public":
                all_annotations = all_annotations.filter(status=1)
            if this_user_is_superexpert:
                if checked == "unchecked":
                    all_annotations = all_annotations.filter(validation_complete=False)
                elif checked == "confirmed":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=False)
                elif checked == "revised":
                    all_annotations = all_annotations.filter(validation_complete=True, revise=True)
                if final_status == "flagged":
                    all_annotations = all_annotations.filter(report__in=flagged_final_reports)
                elif final_status == "hidden":
                    all_annotations = all_annotations.filter(report__in=hidden_final_reports)
                elif final_status == "public":
                    all_annotations = all_annotations.filter(report__in=public_final_reports).exclude(report__in=flagged_final_reports).exclude(report__in=hidden_final_reports)
        if all_annotations:
            all_annotations = all_annotations.order_by('report__creation_time')
            if orderby == "site_score":
                all_annotations = all_annotations.order_by('site_certainty_category')
            elif orderby == "tiger_score":
                all_annotations = all_annotations.order_by('tiger_certainty_category')
        paginator = Paginator(all_annotations, int(tasks_per_page))
        page = request.GET.get('page', 1)
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        page_query = all_annotations.filter(id__in=[object.id for object in objects])
        this_formset = AnnotationFormset(queryset=page_query)
        args['formset'] = this_formset
        args['objects'] = objects
        args['pages'] = range(1, objects.paginator.num_pages+1)
        #current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).count()
        current_pending = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=False).filter(report__type='adult').count()
        args['n_pending'] = current_pending
        #n_complete = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).count()
        n_complete = ExpertReportAnnotation.objects.filter(user=this_user).filter(validation_complete=True).filter(report__type='adult').count()
        args['n_complete'] = n_complete
        args['n_total'] = n_complete + current_pending
        args['year'] = year
        args['orderby'] = orderby
        args['tiger_certainty'] = tiger_certainty
        args['site_certainty'] = site_certainty
        args['pending'] = pending
        args['checked'] = checked
        args['status'] = status
        args['final_status'] = final_status
        args['version_uuid'] = version_uuid
        args['linked_id'] = linked_id
        args['tags_filter'] = tags_filter
        args['my_version_uuids'] = my_version_uuids
        args['my_linked_ids'] = my_linked_ids
        args['tasks_per_page'] = tasks_per_page
        args['note_language'] = note_language
        args['scroll_position'] = scroll_position
        args['edit_mode'] = edit_mode
        n_query_records = all_annotations.count()
        args['n_query_records'] = n_query_records
        args['tasks_per_page_choices'] = range(5, min(100, n_query_records)+1, 5)
        return render(request, 'tigacrafting/expert_report_annotation.html' if this_user_is_expert else 'tigacrafting/superexpert_report_annotation.html', args)
    else:
        return HttpResponse("You need to be logged in as an expert member to view this page. If you have have been recruited as an expert and have lost your log-in credentials, please contact MoveLab.")


@login_required
def expert_report_status(request, reports_per_page=10, version_uuid=None, linked_id=None):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        version_uuid = request.GET.get('version_uuid', version_uuid)
        reports_per_page = request.GET.get('reports_per_page', reports_per_page)
        #all_reports_version_uuids = Report.objects.filter(type__in=['adult', 'site']).values('version_UUID')
        all_reports_version_uuids = Report.objects.filter(type='adult').values('version_UUID')
        #these_reports = Report.objects.exclude(creation_time__year=2014).exclude(hide=True).exclude(photos__isnull=True).filter(type__in=['adult', 'site'])
        these_reports = Report.objects.exclude(creation_time__year=2014).exclude(hide=True).exclude(photos__isnull=True).filter(type='adult')
        if version_uuid and version_uuid != 'na':
            reports = Report.objects.filter(version_UUID=version_uuid)
            n_reports = 1
        elif linked_id and linked_id != 'na':
            reports = Report.objects.filter(linked_id=linked_id)
            n_reports = 1
        else:
            reports = filter_reports(these_reports, sort=False)
            n_reports = len(reports)
        paginator = Paginator(reports, int(reports_per_page))
        page = request.GET.get('page', 1)
        try:
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)
        paged_reports = Report.objects.filter(version_UUID__in=[object.version_UUID for object in objects])
        reports_per_page_choices = range(0, min(1000, n_reports)+1, 25)
        context = {'reports': paged_reports, 'all_reports_version_uuids': all_reports_version_uuids, 'version_uuid': version_uuid, 'reports_per_page_choices': reports_per_page_choices}
        context['objects'] = objects
        context['pages'] = range(1, objects.paginator.num_pages+1)

        return render(request, 'tigacrafting/expert_report_status.html', context)
    else:
        return HttpResponseRedirect(reverse('login'))


@login_required
def expert_status(request):
    this_user = request.user
    if this_user.groups.filter(Q(name='superexpert') | Q(name='movelab')).exists():
        groups = Group.objects.filter(name__in=['expert', 'superexpert'])
        for group in groups:
            for user in group.user_set.all():
                if not UserStat.objects.filter(user=user).exists():
                    us = UserStat(user=user)
                    us.save()
        return render(request, 'tigacrafting/expert_status.html', {'groups': groups})
    else:
        return HttpResponseRedirect(reverse('login'))

@login_required
def picture_validation(request,tasks_per_page='10',visibility='visible', usr_note='', type='all'):
    args = {}
    args.update(csrf(request))
    PictureValidationFormSet = modelformset_factory(Report, form=PhotoGrid, extra=0)
    if request.method == 'POST':
        save_formset = request.POST.get('save_formset', "F")
        tasks_per_page = request.POST.get('tasks_per_page', tasks_per_page)
        if save_formset == "T":
            formset = PictureValidationFormSet(request.POST)
            if formset.is_valid():
                for f in formset:
                    report = f.save(commit=False)
                    #check that the report hasn't been assigned to anyone before saving, as a precaution to not hide assigned reports
                    who_has = report.get_who_has()
                    if who_has == '':
                        report.save()
        page = request.POST.get('page')
        visibility = request.POST.get('visibility')
        usr_note = request.POST.get('usr_note')
        type = request.POST.get('type', type)
        if not page:
            page = '1'
        return HttpResponseRedirect(reverse('picture_validation') + '?page=' + page + '&tasks_per_page='+tasks_per_page + '&visibility=' + visibility + '&usr_note=' + urllib.quote_plus(usr_note) + '&type=' + type)
    else:
        tasks_per_page = request.GET.get('tasks_per_page', tasks_per_page)
        type = request.GET.get('type', type)
        visibility = request.GET.get('visibility', visibility)
        usr_note = request.GET.get('usr_note', usr_note)

    # #345 is a special tag to exclude reports
    #reports_imbornal = ReportResponse.objects.filter( Q(question='Is this a storm drain or sewer?',answer='Yes') | Q(question=u'\xc9s un embornal o claveguera?',answer=u'S\xed') | Q(question=u'\xbfEs un imbornal o alcantarilla?',answer=u'S\xed') | Q(question='Selecciona lloc de cria',answer='Embornals') | Q(question='Selecciona lloc de cria',answer='Embornal o similar') | Q(question='Tipo de lugar de cría', answer='Sumidero o imbornal') | Q(question='Tipo de lugar de cría', answer='Sumideros') | Q(question='Type of breeding site', answer='Storm drain') |  Q(question='Type of breeding site', answer='Storm drain or similar receptacle')).exclude(report__creation_time__year=2014).values('report').distinct()
    reports_imbornal = ReportResponse.objects.filter(
        Q(question='Is this a storm drain or sewer?', answer='Yes') | Q(question=u'\xc9s un embornal o claveguera?',
                                                                        answer=u'S\xed') | Q(
            question=u'\xbfEs un imbornal o alcantarilla?', answer=u'S\xed') | Q(question='Selecciona lloc de cria',
                                                                                 answer='Embornals') | Q(
            question='Selecciona lloc de cria', answer='Embornal o similar') | Q(question='Tipo de lugar de cría',
                                                                                 answer='Sumidero o imbornal') | Q(
            question='Tipo de lugar de cría', answer='Sumideros') | Q(question='Type of breeding site',
                                                                      answer='Storm drain') | Q(
            question='Type of breeding site', answer='Storm drain or similar receptacle')).values('report').distinct()

    new_reports_unfiltered_adults = Report.objects.exclude(creation_time__year=2014).exclude(type='site').exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
    #new_reports_unfiltered_sites_embornal = Report.objects.exclude(creation_time__year=2014).exclude(type='adult').filter(version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
    new_reports_unfiltered_sites_embornal = Report.objects.exclude(type='adult').filter(version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-creation_time')
    #new_reports_unfiltered_sites_other = Report.objects.exclude(creation_time__year=2014).exclude(type='adult').exclude(version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
    new_reports_unfiltered_sites_other = Report.objects.exclude(type='adult').exclude(version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-creation_time')

    new_reports_unfiltered_sites = new_reports_unfiltered_sites_embornal | new_reports_unfiltered_sites_other

    #new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites_embornal
    new_reports_unfiltered = new_reports_unfiltered_adults | new_reports_unfiltered_sites
    #new_reports_unfiltered = filter(lambda x: not x.deleted and x.latest_version, new_reports_unfiltered)

    #new_reports_unfiltered = Report.objects.exclude(creation_time__year=2014).exclude(note__icontains='#345').exclude(photos=None).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')
    if type == 'adult':
        #new_reports_unfiltered = new_reports_unfiltered.exclude(type='site')
        new_reports_unfiltered = new_reports_unfiltered_adults
    elif type == 'site':
        #new_reports_unfiltered = new_reports_unfiltered.exclude(type='adult')
        new_reports_unfiltered = new_reports_unfiltered_sites_embornal
    elif type == 'site-o':
        new_reports_unfiltered = new_reports_unfiltered_sites_other
    if visibility == 'visible':
        new_reports_unfiltered = new_reports_unfiltered.exclude(hide=True)
    elif visibility == 'hidden':
        new_reports_unfiltered = new_reports_unfiltered.exclude(hide=False)
    if usr_note and usr_note != '':
        new_reports_unfiltered = new_reports_unfiltered.filter(note__icontains=usr_note)

    new_reports_unfiltered = filter_reports(new_reports_unfiltered,False)

    paginator = Paginator(new_reports_unfiltered, int(tasks_per_page))
    page = request.GET.get('page', 1)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    page_query = Report.objects.filter(version_UUID__in=[object.version_UUID for object in objects]).order_by('-creation_time')
    this_formset = PictureValidationFormSet(queryset=page_query)
    args['formset'] = this_formset
    args['objects'] = objects
    args['pages'] = range(1, objects.paginator.num_pages + 1)
    args['new_reports_unfiltered'] = page_query
    args['tasks_per_page'] = tasks_per_page
    args['visibility'] = visibility
    args['usr_note'] = usr_note
    args['type'] = type
    type_readable = ''
    if type == 'site':
        type_readable = "Breeding sites - Storm drains"
    elif type == 'site-o':
        type_readable = "Breeding sites - Other"
    elif type == 'adult':
        type_readable = "Adults"
    elif type == 'all':
        type_readable = "All"
    args['type_readable'] = type_readable
    #n_query_records = new_reports_unfiltered.count()
    n_query_records = len(new_reports_unfiltered)
    args['n_query_records'] = n_query_records
    args['tasks_per_page_choices'] = range(5, min(100, n_query_records) + 1, 5)
    #return render(request, 'tigacrafting/photo_grid.html', {'new_reports_unfiltered' : page_query})
    return render(request, 'tigacrafting/photo_grid.html', args)