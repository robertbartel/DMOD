# UpdateMessageResponse

**Title:** UpdateMessageResponse

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |

**Description:** The subtype of ::class:`Response` appropriate for ::class:`UpdateMessage` objects.

<details>
<summary><strong> <a name="success"></a>1. [Required] Property UpdateMessageResponse > success</strong>

</summary>
<blockquote>

**Title:** Success

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | Yes       |

**Description:** Whether this indicates a successful result.

</blockquote>
</details>

<details>
<summary><strong> <a name="reason"></a>2. [Required] Property UpdateMessageResponse > reason</strong>

</summary>
<blockquote>

**Title:** Reason

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | Yes      |

**Description:** A very short, high-level summary of the result.

</blockquote>
</details>

<details>
<summary><strong> <a name="message"></a>3. [Optional] Property UpdateMessageResponse > message</strong>

</summary>
<blockquote>

**Title:** Message

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |
| **Default**  | `""`     |

**Description:** An optional, more detailed explanation of the result, which by default is an empty string.

</blockquote>
</details>

<details>
<summary><strong> <a name="data"></a>4. [Optional] Property UpdateMessageResponse > data</strong>

</summary>
<blockquote>

|                           |                                                                           |
| ------------------------- | ------------------------------------------------------------------------- |
| **Type**                  | `object`                                                                  |
| **Required**              | No                                                                        |
| **Additional properties** | [[Any type: allowed]](# "Additional Properties of any type are allowed.") |
| **Defined in**            | #/definitions/UpdateMessageData                                           |

**Description:** An interface class for an object that can be serialized to a dictionary-like format (i.e., potentially a JSON
object) and JSON string format based directly from dumping the aforementioned dictionary-like representation.

Subtypes of `Serializable` should specify their fields following
[`pydantic.BaseModel`](https://docs.pydantic.dev/usage/models/) semantics (see example below).
Notably, `to_dict` and `to_json` will exclude `None` fields and serialize fields using any
provided aliases (i.e.  `pydantic.Field(alias="some_alias")`). Also, enum subtypes are
serialized using their member `name` property.

Objects of this type will also used the JSON string format as their default string representation.

While not strictly enforced (because this probably isn't possible), it is HIGHLY recommended that instance
attribute members of implemented sub-types be of types that are either convertible to strings using the ``str()``
built-in, or are themselves also implementations of ::class:`Serializable`.  The convenience class method
::method:`serialize` will handle serializing any such member objects appropriately, providing a clean interface for
this.

An exception to the aforementioned recommendation is the ::class:`datetime.datetime` type.  Subtype attributes of
::class:`datetime.datetime` type should be parsed and serialized using the pattern returned by the
::method:`get_datetime_str_format` class method.  A reasonable default is provided in the base interface class, but
the pattern can be adjusted either by overriding the class method directly or by having a subtypes set/override
its ::attribute:`_SERIAL_DATETIME_STR_FORMAT` class attribute.  Note that the actual parsing/serialization logic is
left entirely to the subtypes, as many will not need it (and thus should not have to worry about implement another
method or have their superclass bloated by importing the ``datetime`` package).

Example:
```
# specify field as class variable, specify final type using type hint.
# pydantic will try to coerce a field into the specified type, if it can't, a
# `pydantic.ValidationError` is raised.

class User(Serializable):
    id: int
    username: str
    email: str # more appropriately, `pydantic.EmailStr`

>>> user = User(id=1, username="uncle_sam", email="uncle_sam@fake.gov")
>>> user.to_dict() # {"id": 1, "username": "uncle_sam", "email": "uncle_sam@fake.gov"}
>>> user.to_json() # '{"id": 1, "username": "uncle_sam", "email": "uncle_sam@fake.gov"}'
```

<details>
<summary><strong> <a name="data_digest"></a>4.1. [Optional] Property UpdateMessageResponse > data > digest</strong>

</summary>
<blockquote>

**Title:** Digest

|              |          |
| ------------ | -------- |
| **Type**     | `string` |
| **Required** | No       |

</blockquote>
</details>

<details>
<summary><strong> <a name="data_object_found"></a>4.2. [Optional] Property UpdateMessageResponse > data > object_found</strong>

</summary>
<blockquote>

**Title:** Object Found

|              |           |
| ------------ | --------- |
| **Type**     | `boolean` |
| **Required** | No        |

</blockquote>
</details>

</blockquote>
</details>

----------------------------------------------------------------------------------------------------------------------------
