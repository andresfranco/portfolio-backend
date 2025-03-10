from .token import Token, TokenPayload
from .user import UserBase, UserCreate, UserUpdate, UserOut, UserPasswordChange
from .role import RoleBase, RoleOut, RoleUpdate, RoleFilter
from .permission import PermissionBase, PermissionCreate, PermissionUpdate, PermissionOut, PaginatedPermissionResponse, Filter as PermissionFilter
from .language import LanguageBase, LanguageCreate, LanguageUpdate, LanguageOut, Filter as LanguageFilter
from .translation import TranslationBase, TranslationCreate, TranslationUpdate, TranslationOut, Filter as TranslationFilter
from .portfolio import PortfolioBase, PortfolioCreate, PortfolioUpdate, PortfolioOut, PortfolioImageBase, PortfolioImageCreate, PortfolioImageUpdate, PortfolioImageOut, Filter as PortfolioFilter, PaginatedPortfolioResponse
from .section import SectionBase, SectionCreate, SectionUpdate, Section, SectionTextBase, SectionTextCreate, SectionTextUpdate, SectionTextOut, Filter as SectionFilter, PaginatedSectionResponse
from .experience import ExperienceBase, ExperienceCreate, ExperienceUpdate, Experience, ExperienceTextBase, ExperienceTextCreate, ExperienceTextUpdate, ExperienceTextOut, Filter as ExperienceFilter, PaginatedExperienceResponse
from .project import ProjectBase, ProjectCreate, ProjectUpdate, ProjectOut, ProjectTextBase, ProjectTextCreate, ProjectTextUpdate, ProjectTextOut, ProjectImageBase, ProjectImageCreate, ProjectImageUpdate, ProjectImageOut, ProjectAttachmentBase, ProjectAttachmentCreate, ProjectAttachmentUpdate, ProjectAttachmentOut, Filter as ProjectFilter, PaginatedProjectResponse
from .category import CategoryBase, CategoryCreate, CategoryUpdate, CategoryOut, CategoryTextBase, CategoryTextCreate, CategoryTextUpdate, CategoryTextOut, Filter as CategoryFilter, PaginatedCategoryResponse
from .skill import SkillBase, SkillCreate, SkillUpdate, SkillOut, SkillTextBase, SkillTextCreate, SkillTextUpdate, SkillTextOut, Filter as SkillFilter, PaginatedSkillResponse
from .pagination import PaginatedResponse

# Aliases for backward compatibility
Language = LanguageBase
Translation = TranslationBase
Portfolio = PortfolioBase
PortfolioImage = PortfolioImageOut
Section = Section
SectionText = SectionTextOut
Experience = Experience
ExperienceText = ExperienceTextOut
Project = ProjectBase
ProjectImage = ProjectImageOut
ProjectAttachment = ProjectAttachmentOut
ProjectText = ProjectTextOut
Category = CategoryBase
CategoryText = CategoryTextOut
Skill = SkillBase
SkillText = SkillTextOut
